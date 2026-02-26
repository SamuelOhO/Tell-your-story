import { useEffect, useRef, useState } from 'react'
import Button from './components/Button'
import Card from './components/Card'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'
const DEFAULT_QUESTION = '어린 시절 가장 기억에 남는 추억은 무엇인가요?'

async function buildApiError(response) {
    try {
        const body = await response.json()
        if (typeof body?.detail === 'string') return body.detail
        if (Array.isArray(body?.detail) && body.detail.length > 0) return '입력값 형식을 확인해주세요.'
    } catch {
        // Ignore JSON parsing error and fallback to generic message.
    }

    return `요청 처리에 실패했습니다. (${response.status})`
}

function App() {
    const [userAnswer, setUserAnswer] = useState('')
    const [step, setStep] = useState('welcome') // welcome, interview
    const [conversation, setConversation] = useState([])
    const [currentQuestion, setCurrentQuestion] = useState(DEFAULT_QUESTION)
    const [isLoading, setIsLoading] = useState(false)
    const [errorMessage, setErrorMessage] = useState('')
    const [lastAction, setLastAction] = useState('')
    const historyContainerRef = useRef(null)

    useEffect(() => {
        if (!historyContainerRef.current) return
        historyContainerRef.current.scrollTop = historyContainerRef.current.scrollHeight
    }, [conversation])

    const handleStart = async () => {
        setErrorMessage('')
        setLastAction('start')
        setIsLoading(true)

        try {
            const response = await fetch(`${API_BASE_URL}/interview/start`, {
                method: 'POST',
            })

            if (!response.ok) {
                throw new Error(await buildApiError(response))
            }

            const data = await response.json()
            setConversation([])
            setCurrentQuestion(data.first_question || DEFAULT_QUESTION)
            setStep('interview')
        } catch (error) {
            console.error(error)
            setErrorMessage(error.message || '인터뷰를 시작하지 못했습니다. 잠시 후 다시 시도해주세요.')
        } finally {
            setIsLoading(false)
        }
    }

    const handleSubmit = async () => {
        const normalizedAnswer = userAnswer.trim()
        if (!normalizedAnswer || isLoading) return

        setErrorMessage('')
        setLastAction('submit')
        setIsLoading(true)
        try {
            const response = await fetch(`${API_BASE_URL}/interview/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_text: normalizedAnswer,
                    conversation_history: conversation
                }),
            })

            if (!response.ok) {
                throw new Error(await buildApiError(response))
            }

            const data = await response.json()
            if (!data?.ai_text || !data?.next_question) {
                throw new Error('서버 응답 형식이 올바르지 않습니다.')
            }

            setConversation((prev) => [
                ...prev,
                { role: 'user', text: normalizedAnswer },
                { role: 'ai', text: data.ai_text }
            ])
            setUserAnswer('')
            setCurrentQuestion(data.next_question)
        } catch (error) {
            console.error(error)
            setErrorMessage(error.message || '오류가 발생했습니다. 다시 시도해주세요.')
        } finally {
            setIsLoading(false)
        }
    }

    const handleRetry = async () => {
        if (isLoading) return
        if (lastAction === 'start') {
            await handleStart()
            return
        }
        if (lastAction === 'submit') {
            await handleSubmit()
        }
    }

    const handleTextareaKeyDown = (event) => {
        if (event.key !== 'Enter' || event.shiftKey) return
        event.preventDefault()
        handleSubmit()
    }

    return (
        <div className="min-h-screen bg-slate-50 flex flex-col items-center p-4 py-10 font-sans">
            <header className="mb-10 text-center">
                <h1 className="text-4xl md:text-5xl font-bold text-slate-800 mb-4">자서전 만들기</h1>
                <p className="text-xl text-slate-600">당신의 소중한 이야기를 들려주세요</p>
            </header>

            <main className="w-full max-w-2xl">
                {step === 'welcome' && (
                    <Card className="text-center space-y-8">
                        <p className="text-2xl text-slate-700 leading-relaxed">
                            안녕하세요.<br />
                            지금부터 어르신의 살아온 이야기를<br />
                            책으로 만들어드리겠습니다.
                        </p>
                        <div className="pt-4">
                            <Button onClick={handleStart} disabled={isLoading}>
                                {isLoading ? '준비 중...' : '시작하기'}
                            </Button>
                        </div>
                        {errorMessage && (
                            <div className="space-y-3 rounded-lg bg-rose-50 px-4 py-3 text-base text-rose-700">
                                <p>{errorMessage}</p>
                                <Button onClick={handleRetry} className="px-5 py-2 text-base" disabled={isLoading}>
                                    다시 시도
                                </Button>
                            </div>
                        )}
                    </Card>
                )}

                {step === 'interview' && (
                    <Card className="space-y-6">
                        <div className="space-y-4 text-center">
                            <h2 className="text-2xl font-semibold text-slate-800">질문</h2>
                            <p className="text-2xl md:text-3xl text-slate-900 font-medium leading-relaxed">
                                &quot;{currentQuestion}&quot;
                            </p>
                        </div>

                        {errorMessage && (
                            <div className="space-y-3 rounded-lg bg-rose-50 px-4 py-3 text-base text-rose-700">
                                <p>{errorMessage}</p>
                                <Button onClick={handleRetry} className="px-5 py-2 text-base" disabled={isLoading}>
                                    다시 시도
                                </Button>
                            </div>
                        )}

                        <section className="space-y-3">
                            <h3 className="text-lg font-semibold text-slate-800">대화 기록</h3>
                            {conversation.length === 0 ? (
                                <p className="text-slate-500">아직 대화 기록이 없습니다.</p>
                            ) : (
                                <div ref={historyContainerRef} className="max-h-72 space-y-3 overflow-y-auto rounded-xl border border-slate-200 bg-slate-50 p-4">
                                    {conversation.map((message, index) => {
                                        const isUser = message.role === 'user'
                                        return (
                                            <div key={`${message.role}-${index}`} className="space-y-1">
                                                <p className="text-sm font-semibold text-slate-500">
                                                    {isUser ? '나' : 'AI 작가'}
                                                </p>
                                                <p className={`rounded-lg px-3 py-2 text-base leading-relaxed ${isUser ? 'bg-white text-slate-800' : 'bg-blue-50 text-slate-800'}`}>
                                                    {message.text}
                                                </p>
                                            </div>
                                        )
                                    })}
                                </div>
                            )}
                        </section>

                        <div className="flex flex-col space-y-4">
                            <textarea
                                className="w-full p-4 border border-slate-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none text-lg"
                                rows="4"
                                placeholder="답변을 입력해주세요..."
                                value={userAnswer}
                                onChange={(e) => setUserAnswer(e.target.value)}
                                onKeyDown={handleTextareaKeyDown}
                                disabled={isLoading}
                            />
                            <p className="text-sm text-slate-500">Enter로 전송, Shift+Enter로 줄바꿈</p>
                            <div className="flex justify-end">
                                <Button onClick={handleSubmit} disabled={!userAnswer.trim() || isLoading}>
                                    {isLoading ? "생각 중..." : "답변하기"}
                                </Button>
                            </div>
                        </div>
                    </Card>
                )}
            </main>
        </div>
    )
}

export default App
