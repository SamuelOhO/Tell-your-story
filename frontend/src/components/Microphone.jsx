export default function Microphone({ onStart, onStop, isRecording }) {
    return (
        <button
            onClick={isRecording ? onStop : onStart}
            className={`w-32 h-32 rounded-full flex items-center justify-center transition-all duration-300 ${isRecording
                    ? 'bg-red-500 animate-pulse shadow-[0_0_20px_rgba(239,68,68,0.6)]'
                    : 'bg-blue-600 hover:bg-blue-700 shadow-lg'
                }`}
            aria-label={isRecording ? "Stop Recording" : "Start Recording"}
        >
            <svg
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth={1.5}
                stroke="currentColor"
                className="w-16 h-16 text-white"
            >
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 18.75a6 6 0 006-6v-1.5m-6 7.5a6 6 0 01-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 15.75a3 3 0 01-3-3V4.5a3 3 0 116 0v8.25a3 3 0 01-3 3z" />
            </svg>
        </button>
    )
}
