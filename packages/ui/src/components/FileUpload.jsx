import React, { useRef } from "react";

export default function FileUpload({ onUpload }) {
  const ref = useRef();
  return (
    <div>
      <input
        type="file"
        ref={ref}
        className="hidden"
        onChange={(e) => onUpload(e.target.files[0])}
      />
      <button
        className="bg-green-500 text-white px-3 py-1 rounded hover:bg-green-600"
        onClick={() => ref.current.click()}
      >
        Upload File
      </button>
    </div>
  );
}

