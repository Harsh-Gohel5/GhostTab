export function GhostMark() {
  return (
    <svg
      className="ghost-logo"
      viewBox="0 0 40 40"
      fill="none"
      aria-hidden="true"
    >
      <path
        d="M8 31V19a12 12 0 0 1 24 0v12c-2 3-4-1-6-1s-4 4-6 4-4-4-6-4-4 4-6 1Z"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinejoin="round"
        className="ghost-body"
      />
      <g className="ghost-eyes">
        <ellipse cx="15.5" cy="19" rx="1.5" ry="2" fill="currentColor" />
        <ellipse cx="24.5" cy="19" rx="1.5" ry="2" fill="currentColor" />
      </g>
      <path
        className="ghost-smile"
        d="M17 24q3 3 6 0"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
      <circle className="ghost-cheek" cx="12" cy="23" r="2" />
      <circle className="ghost-cheek" cx="28" cy="23" r="2" />
      <g className="ghost-night-hat">
        <path
          d="m9 12 8-11 3 9 7 3Z"
          fill="var(--logo-hat)"
          stroke="currentColor"
          strokeLinejoin="round"
        />
        <path
          d="m10 11 17 3"
          stroke="var(--logo-spark)"
          strokeWidth="2"
          strokeLinecap="round"
        />
        <path d="m33 3 1 3 3 1-3 1-1 3-1-3-3-1 3-1Z" fill="var(--logo-spark)" />
      </g>
    </svg>
  );
}
