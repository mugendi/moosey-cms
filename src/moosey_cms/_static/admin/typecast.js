/**
 * Copyright (c) 2026 Anthony Mugendi
 * 
 * This software is released under the MIT License.
 * https://opensource.org/licenses/MIT
 */


/**
 * autoTypecast.js
 *
 * Automatically detects and converts string (or mixed) input into the
 * most appropriate JavaScript type: number, boolean, null, undefined,
 * Date, Array, Object, or string (fallback).
 *
 * Usage:
 *   const { typecast, typecastObject } = require('./autoTypecast');
 *   typecast("42")          // 42 (number)
 *   typecast("true")        // true (boolean)
 *   typecast("null")        // null
 *   typecast("2024-01-15")  // Date object
 *   typecast('{"a":1}')     // { a: 1 }
 *   typecastObject({ id: "1", active: "true", createdAt: "01/15/2024" })
 */
 
// ---- Date format patterns -------------------------------------------------
// Each entry: regex to match + a parser that returns a valid Date or null.
const DATE_PATTERNS = [
  // ISO 8601: 2024-01-15, 2024-01-15T10:30:00Z, 2024-01-15T10:30:00.000+02:00
  {
    regex: /^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}(:\d{2}(\.\d+)?)?(Z|[+-]\d{2}:?\d{2})?)?$/,
    parse: (v) => new Date(v),
  },
  // yyyy/mm/dd
  {
    regex: /^\d{4}\/\d{1,2}\/\d{1,2}$/,
    parse: (v) => {
      const [y, m, d] = v.split('/').map(Number);
      return new Date(y, m - 1, d);
    },
  },
  // mm/dd/yyyy or m/d/yyyy (US style)
  {
    regex: /^\d{1,2}\/\d{1,2}\/\d{4}$/,
    parse: (v) => {
      const [m, d, y] = v.split('/').map(Number);
      return new Date(y, m - 1, d);
    },
  },
  // dd-mm-yyyy or dd.mm.yyyy (common EU style)
  {
    regex: /^\d{1,2}[-.]\d{1,2}[-.]\d{4}$/,
    parse: (v) => {
      const [d, m, y] = v.split(/[-.]/).map(Number);
      return new Date(y, m - 1, d);
    },
  },
  // yyyy-mm (month only)
  {
    regex: /^\d{4}-\d{2}$/,
    parse: (v) => {
      const [y, m] = v.split('-').map(Number);
      return new Date(y, m - 1, 1);
    },
  },
  // "Month D, YYYY" e.g. "January 15, 2024" / "Jan 15, 2024"
  {
    regex: /^[A-Za-z]{3,9}\.?\s+\d{1,2},?\s+\d{4}$/,
    parse: (v) => new Date(v),
  },
  // "D Month YYYY" e.g. "15 January 2024"
  {
    regex: /^\d{1,2}\s+[A-Za-z]{3,9}\.?\s+\d{4}$/,
    parse: (v) => new Date(v),
  },
  // Unix timestamp in seconds (10 digits) or ms (13 digits) as a numeric string
  {
    regex: /^\d{10}$/,
    parse: (v) => new Date(Number(v) * 1000),
  },
  {
    regex: /^\d{13}$/,
    parse: (v) => new Date(Number(v)),
  },
];
 
function isValidDate(d) {
  return d instanceof Date && !isNaN(d.getTime());
}
 
function tryParseDate(str) {
  const trimmed = str.trim();
  for (const { regex, parse } of DATE_PATTERNS) {
    if (regex.test(trimmed)) {
      const d = parse(trimmed);
      if (isValidDate(d)) return d;
    }
  }
  return null;
}
 
// ---- Core typecast function ------------------------------------------------
 
/**
 * Attempts to convert a single value to its most appropriate type.
 * @param {*} value - the input value (usually a string, but handles any type)
 * @param {Object} [options]
 * @param {boolean} [options.parseDates=true] - whether to attempt date parsing
 * @param {boolean} [options.parseJSON=true] - whether to attempt JSON parsing for objects/arrays
 * @param {boolean} [options.emptyStringAsNull=false] - treat "" as null
 * @returns {*} the typecast value
 */
function typecast(value, options = {}) {
  const {
    parseDates = true,
    parseJSON = true,
    emptyStringAsNull = false,
  } = options;
 
  // Already non-string types: recurse into arrays/objects, leave rest as-is
  if (value === null || value === undefined) return value;
  if (typeof value === 'number' || typeof value === 'boolean' || value instanceof Date) {
    return value;
  }
  if (Array.isArray(value)) {
    return value.map((v) => typecast(v, options));
  }
  if (typeof value === 'object') {
    return typecastObject(value, options);
  }
  if (typeof value !== 'string') return value;
 
  const trimmed = value.trim();
 
  // Empty string
  if (trimmed === '') return emptyStringAsNull ? null : value;
 
  // null / undefined literals
  const lower = trimmed.toLowerCase();
  if (lower === 'null') return null;
  if (lower === 'undefined') return undefined;
  if (lower === 'nan') return NaN;
 
  // Boolean literals
  if (lower === 'true') return true;
  if (lower === 'false') return false;
 
  // Numbers (int, float, negative, exponential, but not hex/octal ambiguity)
  // Avoid treating things like "1,234" as numbers unless comma-stripped explicitly.
  if (/^[+-]?(\d+\.?\d*|\.\d+)(e[+-]?\d+)?$/i.test(trimmed)) {
    const num = Number(trimmed);
    if (!Number.isNaN(num)) return num;
  }
 
  // Dates
  if (parseDates) {
    const date = tryParseDate(trimmed);
    if (date) return date;
  }
 
  // JSON objects / arrays
  if (parseJSON && (trimmed.startsWith('{') || trimmed.startsWith('['))) {
    try {
      const parsed = JSON.parse(trimmed);
      return typecast(parsed, options);
    } catch (e) {
      // fall through to string
    }
  }
 
  // Fallback: return original string
  return value;
}
 
/**
 * Recursively typecasts every value in a plain object.
 * @param {Object} obj
 * @param {Object} [options] - see typecast() for options
 * @returns {Object} a new object with typecast values
 */
function typecastObject(obj, options = {}) {
  if (obj === null || typeof obj !== 'object') return typecast(obj, options);
  if (Array.isArray(obj)) return obj.map((v) => typecast(v, options));
 
  const result = {};
  for (const [key, val] of Object.entries(obj)) {
    result[key] = typecast(val, options);
  }
  return result;
}
 
/**
 * Typecasts every row/value in an array of objects (e.g. CSV rows).
 * @param {Array<Object>} rows
 * @param {Object} [options]
 * @returns {Array<Object>}
 */
function typecastRows(rows, options = {}) {
  return rows.map((row) => typecastObject(row, options));
}