export default function Card({ children, className = '' }) {
    return (
        <section className={`story-card ${className}`}>
            {children}
        </section>
    )
}
