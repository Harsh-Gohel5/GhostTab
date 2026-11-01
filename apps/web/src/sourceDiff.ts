export type DiffLine = {
  kind: "unchanged" | "removed" | "added";
  text: string;
};

// Bound quadratic work for large documents. Full versions remain available.
export function sourceDiff(before: string, after: string): DiffLine[] {
  if (before === after) return [{ kind: "unchanged", text: before }];
  const left = before.split("\n");
  const right = after.split("\n");
  if (left.length > 200 || right.length > 200)
    return [
      { kind: "removed", text: before },
      { kind: "added", text: after },
    ];
  const lengths = Array.from(
    { length: left.length + 1 },
    () => new Uint16Array(right.length + 1),
  );
  for (let i = left.length - 1; i >= 0; i--)
    for (let j = right.length - 1; j >= 0; j--)
      lengths[i][j] =
        left[i] === right[j]
          ? lengths[i + 1][j + 1] + 1
          : Math.max(lengths[i + 1][j], lengths[i][j + 1]);
  const result: DiffLine[] = [];
  let i = 0;
  let j = 0;
  while (i < left.length || j < right.length) {
    if (i < left.length && j < right.length && left[i] === right[j]) {
      result.push({ kind: "unchanged", text: left[i++] });
      j++;
    } else if (
      i < left.length &&
      (j === right.length || lengths[i + 1][j] >= lengths[i][j + 1])
    ) {
      result.push({ kind: "removed", text: left[i++] });
    } else {
      result.push({ kind: "added", text: right[j++] });
    }
  }
  return result;
}
