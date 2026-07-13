use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::PyBytes;

const TAG_END: u8 = 0;
const TAG_BYTE: u8 = 1;
const TAG_SHORT: u8 = 2;
const TAG_INT: u8 = 3;
const TAG_LONG: u8 = 4;
const TAG_FLOAT: u8 = 5;
const TAG_DOUBLE: u8 = 6;
const TAG_BYTE_ARRAY: u8 = 7;
const TAG_STRING: u8 = 8;
const TAG_LIST: u8 = 9;
const TAG_COMPOUND: u8 = 10;
const TAG_INT_ARRAY: u8 = 11;
const TAG_LONG_ARRAY: u8 = 12;

type NativeBlock = (String, Vec<(String, i64)>, Vec<(String, String)>, bool);
type ParsedResult = ((usize, usize, usize), Vec<u8>, Vec<NativeBlock>);
type NativeResult = ((usize, usize, usize), Py<PyBytes>, Vec<NativeBlock>);

#[derive(Default)]
struct Decoded {
    size: Option<(usize, usize, usize)>,
    primary: Option<Vec<i32>>,
    water: Option<Vec<i32>>,
    palette: Option<Vec<PaletteBlock>>,
    unsupported: bool,
}

#[derive(Default)]
struct PaletteBlock {
    name: Option<String>,
    integer_states: Vec<(String, i64)>,
    string_states: Vec<(String, String)>,
}

struct Reader<'a> {
    data: &'a [u8],
    position: usize,
}

impl<'a> Reader<'a> {
    fn new(data: &'a [u8]) -> Self {
        Self { data, position: 0 }
    }

    fn take(&mut self, length: usize) -> Result<&'a [u8], String> {
        let end = self
            .position
            .checked_add(length)
            .ok_or_else(|| "NBT offset overflow".to_string())?;
        if end > self.data.len() {
            return Err("truncated NBT payload".to_string());
        }
        let value = &self.data[self.position..end];
        self.position = end;
        Ok(value)
    }

    fn u8(&mut self) -> Result<u8, String> {
        Ok(self.take(1)?[0])
    }

    fn i8(&mut self) -> Result<i8, String> {
        Ok(self.u8()? as i8)
    }

    fn i16(&mut self) -> Result<i16, String> {
        let bytes: [u8; 2] = self.take(2)?.try_into().unwrap();
        Ok(i16::from_le_bytes(bytes))
    }

    fn i32(&mut self) -> Result<i32, String> {
        let bytes: [u8; 4] = self.take(4)?.try_into().unwrap();
        Ok(i32::from_le_bytes(bytes))
    }

    fn i64(&mut self) -> Result<i64, String> {
        let bytes: [u8; 8] = self.take(8)?.try_into().unwrap();
        Ok(i64::from_le_bytes(bytes))
    }

    fn length(&mut self) -> Result<usize, String> {
        let value = self.i32()?;
        usize::try_from(value).map_err(|_| "negative NBT collection length".to_string())
    }

    fn string(&mut self) -> Result<String, String> {
        let length = self.i16()?;
        let length =
            usize::try_from(length).map_err(|_| "negative NBT string length".to_string())?;
        String::from_utf8(self.take(length)?.to_vec())
            .map_err(|_| "invalid UTF-8 in NBT string".to_string())
    }

    fn named_tag(&mut self) -> Result<(u8, String), String> {
        let tag = self.u8()?;
        if tag == TAG_END {
            return Ok((tag, String::new()));
        }
        Ok((tag, self.string()?))
    }

    fn skip_bytes(&mut self, item_size: usize, count: usize) -> Result<(), String> {
        let length = item_size
            .checked_mul(count)
            .ok_or_else(|| "NBT collection size overflow".to_string())?;
        self.take(length)?;
        Ok(())
    }

    fn skip_payload(&mut self, tag: u8) -> Result<(), String> {
        match tag {
            TAG_BYTE => self.skip_bytes(1, 1),
            TAG_SHORT => self.skip_bytes(2, 1),
            TAG_INT | TAG_FLOAT => self.skip_bytes(4, 1),
            TAG_LONG | TAG_DOUBLE => self.skip_bytes(8, 1),
            TAG_BYTE_ARRAY => {
                let length = self.length()?;
                self.skip_bytes(1, length)
            }
            TAG_STRING => {
                self.string()?;
                Ok(())
            }
            TAG_LIST => {
                let child_tag = self.u8()?;
                let length = self.length()?;
                for _ in 0..length {
                    self.skip_payload(child_tag)?;
                }
                Ok(())
            }
            TAG_COMPOUND => {
                loop {
                    let (child_tag, _) = self.named_tag()?;
                    if child_tag == TAG_END {
                        break;
                    }
                    self.skip_payload(child_tag)?;
                }
                Ok(())
            }
            TAG_INT_ARRAY => {
                let length = self.length()?;
                self.skip_bytes(4, length)
            }
            TAG_LONG_ARRAY => {
                let length = self.length()?;
                self.skip_bytes(8, length)
            }
            _ => Err(format!("unknown NBT tag id {tag}")),
        }
    }

    fn parse_int_list(&mut self) -> Result<Vec<i32>, String> {
        let child_tag = self.u8()?;
        let length = self.length()?;
        if child_tag != TAG_INT {
            return Err("expected an NBT list of ints".to_string());
        }
        let mut values = Vec::with_capacity(length);
        for _ in 0..length {
            values.push(self.i32()?);
        }
        Ok(values)
    }

    fn parse_block_indices(&mut self, decoded: &mut Decoded) -> Result<(), String> {
        let child_tag = self.u8()?;
        let length = self.length()?;
        if child_tag != TAG_LIST || length != 2 {
            return Err("block_indices must contain two NBT int lists".to_string());
        }
        decoded.primary = Some(self.parse_int_list()?);
        decoded.water = Some(self.parse_int_list()?);
        Ok(())
    }

    fn parse_entities(&mut self, decoded: &mut Decoded) -> Result<(), String> {
        let child_tag = self.u8()?;
        let length = self.length()?;
        if length != 0 {
            decoded.unsupported = true;
        }
        for _ in 0..length {
            self.skip_payload(child_tag)?;
        }
        Ok(())
    }

    fn parse_states(
        &mut self,
        block: &mut PaletteBlock,
        decoded: &mut Decoded,
    ) -> Result<(), String> {
        loop {
            let (tag, name) = self.named_tag()?;
            match tag {
                TAG_END => return Ok(()),
                TAG_BYTE => block.integer_states.push((name, self.i8()? as i64)),
                TAG_SHORT => block.integer_states.push((name, self.i16()? as i64)),
                TAG_INT => block.integer_states.push((name, self.i32()? as i64)),
                TAG_LONG => block.integer_states.push((name, self.i64()?)),
                TAG_STRING => block.string_states.push((name, self.string()?)),
                _ => {
                    decoded.unsupported = true;
                    self.skip_payload(tag)?;
                }
            }
        }
    }

    fn parse_palette_block(&mut self, decoded: &mut Decoded) -> Result<PaletteBlock, String> {
        let mut block = PaletteBlock::default();
        loop {
            let (tag, name) = self.named_tag()?;
            if tag == TAG_END {
                break;
            }
            match (tag, name.as_str()) {
                (TAG_STRING, "name") => block.name = Some(self.string()?),
                (TAG_COMPOUND, "states") => self.parse_states(&mut block, decoded)?,
                _ => self.skip_payload(tag)?,
            }
        }
        if block.name.is_none() {
            return Err("palette block is missing name".to_string());
        }
        Ok(block)
    }

    fn parse_block_palette(&mut self, decoded: &mut Decoded) -> Result<(), String> {
        let child_tag = self.u8()?;
        let length = self.length()?;
        if child_tag != TAG_COMPOUND {
            return Err("block_palette must be a list of compounds".to_string());
        }
        let mut palette = Vec::with_capacity(length);
        for _ in 0..length {
            palette.push(self.parse_palette_block(decoded)?);
        }
        decoded.palette = Some(palette);
        Ok(())
    }

    fn parse_position_data(&mut self, decoded: &mut Decoded) -> Result<(), String> {
        let (first_tag, _) = self.named_tag()?;
        if first_tag == TAG_END {
            return Ok(());
        }
        decoded.unsupported = true;
        self.skip_payload(first_tag)?;
        loop {
            let (tag, _) = self.named_tag()?;
            if tag == TAG_END {
                return Ok(());
            }
            self.skip_payload(tag)?;
        }
    }

    fn parse_default_palette(&mut self, decoded: &mut Decoded) -> Result<(), String> {
        loop {
            let (tag, name) = self.named_tag()?;
            if tag == TAG_END {
                return Ok(());
            }
            match (tag, name.as_str()) {
                (TAG_LIST, "block_palette") => self.parse_block_palette(decoded)?,
                (TAG_COMPOUND, "block_position_data") => self.parse_position_data(decoded)?,
                _ => self.skip_payload(tag)?,
            }
        }
    }

    fn parse_palette(&mut self, decoded: &mut Decoded) -> Result<(), String> {
        loop {
            let (tag, name) = self.named_tag()?;
            if tag == TAG_END {
                return Ok(());
            }
            match (tag, name.as_str()) {
                (TAG_COMPOUND, "default") => self.parse_default_palette(decoded)?,
                _ => self.skip_payload(tag)?,
            }
        }
    }

    fn parse_structure(&mut self, decoded: &mut Decoded) -> Result<(), String> {
        loop {
            let (tag, name) = self.named_tag()?;
            if tag == TAG_END {
                return Ok(());
            }
            match (tag, name.as_str()) {
                (TAG_LIST, "block_indices") => self.parse_block_indices(decoded)?,
                (TAG_LIST, "entities") => self.parse_entities(decoded)?,
                (TAG_COMPOUND, "palette") => self.parse_palette(decoded)?,
                _ => self.skip_payload(tag)?,
            }
        }
    }

    fn parse_root(&mut self) -> Result<Decoded, String> {
        if self.u8()? != TAG_COMPOUND {
            return Err("mcstructure root must be a compound".to_string());
        }
        self.string()?;
        let mut decoded = Decoded::default();
        loop {
            let (tag, name) = self.named_tag()?;
            if tag == TAG_END {
                break;
            }
            match (tag, name.as_str()) {
                (TAG_INT, "format_version") => {
                    let version = self.i32()?;
                    if version != 1 {
                        return Err(format!("unsupported mcstructure format_version {version}"));
                    }
                }
                (TAG_LIST, "size") => {
                    let size = self.parse_int_list()?;
                    if size.len() != 3 || size.iter().any(|value| *value <= 0) {
                        return Err("mcstructure size must contain three positive ints".to_string());
                    }
                    decoded.size = Some((size[0] as usize, size[1] as usize, size[2] as usize));
                }
                (TAG_COMPOUND, "structure") => self.parse_structure(&mut decoded)?,
                _ => self.skip_payload(tag)?,
            }
        }
        Ok(decoded)
    }
}

fn finish(decoded: Decoded) -> Result<Option<ParsedResult>, String> {
    if decoded.unsupported {
        return Ok(None);
    }
    let size = decoded
        .size
        .ok_or_else(|| "mcstructure is missing size".to_string())?;
    let primary = decoded
        .primary
        .ok_or_else(|| "mcstructure is missing primary block indices".to_string())?;
    let water = decoded
        .water
        .ok_or_else(|| "mcstructure is missing secondary block indices".to_string())?;
    let palette = decoded
        .palette
        .ok_or_else(|| "mcstructure is missing block palette".to_string())?;
    let expected = size
        .0
        .checked_mul(size.1)
        .and_then(|value| value.checked_mul(size.2))
        .ok_or_else(|| "mcstructure volume overflow".to_string())?;
    if primary.len() != expected || water.len() != expected {
        return Err("block index lengths do not match mcstructure size".to_string());
    }

    let mut waterlogged = vec![false; palette.len()];
    for (&primary_index, &water_index) in primary.iter().zip(water.iter()) {
        if primary_index < -1 || (primary_index >= 0 && primary_index as usize >= palette.len()) {
            return Err("primary block index is outside the palette".to_string());
        }
        if water_index < -1 || (water_index >= 0 && water_index as usize >= palette.len()) {
            return Err("secondary block index is outside the palette".to_string());
        }
        if water_index != -1 && primary_index >= 0 {
            waterlogged[primary_index as usize] = true;
        }
    }

    let mut primary_bytes = Vec::with_capacity(primary.len() * 4);
    for value in primary {
        primary_bytes.extend_from_slice(&value.to_le_bytes());
    }
    let blocks = palette
        .into_iter()
        .zip(waterlogged)
        .map(|(block, is_waterlogged)| {
            (
                block.name.unwrap(),
                block.integer_states,
                block.string_states,
                is_waterlogged,
            )
        })
        .collect();
    Ok(Some((size, primary_bytes, blocks)))
}

#[pyfunction]
fn load_simple_structure(py: Python<'_>, data: &[u8]) -> PyResult<Option<NativeResult>> {
    let decoded = Reader::new(data)
        .parse_root()
        .and_then(finish)
        .map_err(PyValueError::new_err)?;
    Ok(
        decoded
            .map(|(size, primary, palette)| (size, PyBytes::new(py, &primary).unbind(), palette)),
    )
}

#[pymodule]
fn _native(module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_function(wrap_pyfunction!(load_simple_structure, module)?)?;
    Ok(())
}
