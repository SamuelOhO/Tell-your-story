export default function Button({ children, onClick, className = '', ...props }) {
    return (
        <button
            onClick={onClick}
            className={`ui-btn ${className}`}
            {...props}
        >
            {children}
        </button>
    )
}
