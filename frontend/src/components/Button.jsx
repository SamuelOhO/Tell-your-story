export default function Button({ children, onClick, className = "", ...props }) {
    return (
        <button
            onClick={onClick}
            className={`px-8 py-4 bg-blue-600 text-white text-xl font-bold rounded-xl shadow-md hover:bg-blue-700 transition-colors focus:outline-none focus:ring-4 focus:ring-blue-300 ${className}`}
            {...props}
        >
            {children}
        </button>
    )
}
