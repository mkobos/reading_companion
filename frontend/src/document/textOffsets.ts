/** Converts a UTF-16 string offset (as reported by DOM Range) to a Unicode
 * code-point offset (as used by Block.text/Passage offsets, matching
 * Python's code-point-based string indexing on the backend). */
export function codePointIndex(str: string, utf16Offset: number): number {
  return Array.from(str.slice(0, utf16Offset)).length;
}

/** Code-point-safe slice — NOT the same as String.prototype.slice, which is
 * UTF-16-indexed and would split surrogate pairs. */
export function codePointSlice(str: string, from: number, to?: number): string {
  return Array.from(str).slice(from, to).join("");
}

/** Code-point-safe length — NOT the same as String.prototype.length, which
 * counts UTF-16 code units and would double-count surrogate pairs. */
export function codePointLength(str: string): number {
  return Array.from(str).length;
}
