const parseBoldSegments = (line) => {
  const segments = [];
  const boldPattern = /\*\*(.+?)\*\*/g;
  let lastIndex = 0;
  let match;

  while ((match = boldPattern.exec(line)) !== null) {
    if (match.index > lastIndex) {
      segments.push({ text: line.slice(lastIndex, match.index), bold: false });
    }
    segments.push({ text: match[1], bold: true });
    lastIndex = match.index + match[0].length;
  }

  if (lastIndex < line.length) {
    segments.push({ text: line.slice(lastIndex), bold: false });
  }

  if (segments.length === 0) {
    segments.push({ text: line, bold: false });
  }

  return segments;
};

export default function FormattedComplaintText({ text, className = '' }) {
  const safeText = typeof text === 'string' ? text : '';
  const lines = safeText.split(/\r?\n/);

  return (
    <span className={className}>
      {lines.map((line, lineIndex) => (
        <span key={`line-${lineIndex}`}>
          {parseBoldSegments(line).map((segment, segmentIndex) => (
            segment.bold ? (
              <strong key={`seg-${lineIndex}-${segmentIndex}`} className="font-semibold text-gray-900">
                {segment.text}
              </strong>
            ) : (
              <span key={`seg-${lineIndex}-${segmentIndex}`}>{segment.text}</span>
            )
          ))}
          {lineIndex < lines.length - 1 ? <br /> : null}
        </span>
      ))}
    </span>
  );
}