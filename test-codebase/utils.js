function toTitleCase(value) {
  return value
    .split(" ")
    .map((word) => word[0].toUpperCase() + word.slice(1).toLowerCase())
    .join(" ");
}

const sum = (a, b) => a + b;

class MathUtil {
  multiply(a, b) {
    return a * b;
  }
}

export { toTitleCase, sum, MathUtil };

