const MATH_SIGNAL =
  /(?:\\(?:frac|dfrac|tfrac|sqrt|sum|prod|int|lim|sin|cos|tan|log|ln|alpha|beta|gamma|delta|theta|pi|sigma|omega|pm|neq|leq|geq|times|cdot)|[=^_]|[<>]\s*[=]|\b(?:sin|cos|tan|log|ln)\b)/i;

function protectCode(text, transform) {
  return text
    .split(/(\`\`\`[\s\S]*?\`\`\`|~~~[\s\S]*?~~~)/g)
    .map((part) => (/^(\`\`\`|~~~)/.test(part) ? part : transform(part)))
    .join("");
}

export function normalizeMathMarkdown(value) {
  if (typeof value !== "string" || !value) return value;

  return protectCode(value, (text) => {
    let result = text;

    result = result
      .replace(/\\\[([\s\S]*?)\\\]/g, (_, math) => "$$\n" + math.trim() + "\n$$")
      .replace(/\\\(([\\s\\S]*?)\\\)/g, (_, math) => "$" + math.trim() + "$");

    result = result.replace(
      /\[\s*([^\[\]\n]{1,300}?)\s*\]/g,
      (match, math) => MATH_SIGNAL.test(math) ? "$" + math.trim() + "$" : match
    );

    result = result.replace(
      /(?<![\w$])([A-Za-z0-9)])(\^|_)(\{[^{}]{1,40}\}|[A-Za-z0-9+-])/g,
      (match, base, operator, exponent) => "$" + base + operator + exponent + "$"
    );

    return result;
  });
}
