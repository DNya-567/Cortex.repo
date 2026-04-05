export function toTitleCase(value) {
  return value
    .split(" ")
    .map((word) => word[0].toUpperCase() + word.slice(1).toLowerCase())
    .join(" ");
}

export const sum = (a, b) => a + b;

export class MathUtil {
  multiply(a, b) {
    return a * b;
  }
}