import { useEffect, useRef, useState } from 'react'
import Button from './components/Button'
import Card from './components/Card'
import Microphone from './components/Microphone'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'
const DEFAULT_QUESTION = '어린 시절 가장 기억에 남는 추억은 무엇인가요?'

function mapErrorType(status) {
    if (status === 422) return 'validation'
    if (status === 401 || status === 403) return 'auth'
    if (status >= 500) return 'server'
    return 'request'
}

function toErrorText(type, message) {
    const prefix = {
        network: '[네트워크]',
        validation: '[입력값]',
        auth: '[인증]',
        server: '[서버]',
        request: '[요청]',
    }[type] ?? '[오류]'
    return `${prefix} ${message}`
}

async function buildApiError(response) {
    const type = mapErrorType(response.status)
    try {
        const body = await response.json()
        if (typeof body?.detail === 'string') return { type, message: body.detail }
        if (Array.isArray(body?.detail) && body.detail.length > 0) {
            return { type, message: '입력값 형식을 확인해주세요.' }
        }
    } catch {
        // Ignore JSON parsing errors.
    }
    return { type, message: `요청 처리에 실패했습니다. (${response.status})` }
}

function App() {
    const [userAnswer, setUserAnswer] = useState('')
    const [step, setStep] = useState('welcome')
    const [sessionId, setSessionId] = useState('')
    const [conversation, setConversation] = useState([])
    const [currentQuestion, setCurrentQuestion] = useState(DEFAULT_QUESTION)
    const [isLoading, setIsLoading] = useState(false)
    const [isRecording, setIsRecording] = useState(false)
    const [isTranscribing, setIsTranscribing] = useState(false)
    const [isDraftLoading, setIsDraftLoading] = useState(false)
    const [errorState, setErrorState] = useState(null)
    const [lastAction, setLastAction] = useState('')
    const [draftText, setDraftText] = useState('')
    const [statusMessage, setStatusMessage] = useState('')
    const historyContainerRef = useRef(null)
    const mediaRecorderRef = useRef(null)
    const streamRef = useRef(null)
    const chunksRef = useRef([])

    useEffect(() => {
        if (!historyContainerRef.current) return
        historyContainerRef.current.scrollTop = historyContainerRef.current.scrollHeight
    }, [conversation])

    const setTypedError = (type, message) => {
        setErrorState({ type, message: toErrorText(type, message) })
    }

    const clearError = () => {
        setErrorState(null)
    }

    const stopStreamTracks = () => {
        if (!streamRef.current) return
        streamRef.current.getTracks().forEach((track) => track.stop())
        streamRef.current = null
    }

    const uploadRecordingBlob = async (blob) => {
        setIsTranscribing(true)
        clearError()
        try {
            const formData = new FormData()
            formData.append('file', blob, 'recording.webm')
            const response = await fetch(`${API_BASE_URL}/interview/stt`, {
                method: 'POST',
                body: formData,
            })
            if (!response.ok) {
                const apiError = await buildApiError(response)
                throw apiError
            }
            const data = await response.json()
            setUserAnswer(data.text || '')
        } catch (error) {
            if (error?.type) setTypedError(error.type, error.message)
            else setTypedError('network', '음성 인식 요청에 실패했습니다.')
        } finally {
            setIsTranscribing(false)
        }
    }

    const handleStartRecording = async () => {
        clearError()
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
            streamRef.current = stream

            const recorder = new MediaRecorder(stream)
            mediaRecorderRef.current = recorder
            chunksRef.current = []

            recorder.ondataavailable = (event) => {
                if (event.data.size > 0) chunksRef.current.push(event.data)
            }

            recorder.onstop = async () => {
                const blob = new Blob(chunksRef.current, { type: 'audio/webm' })
                stopStreamTracks()
                if (blob.size > 0) await uploadRecordingBlob(blob)
            }

            recorder.start()
            setIsRecording(true)
        } catch {
            setTypedError('request', '브라우저 마이크 권한을 확인해주세요.')
        }
    }

    const handleStopRecording = () => {
        if (!mediaRecorderRef.current) return
        mediaRecorderRef.current.stop()
        setIsRecording(false)
    }

    const handleStart = async () => {
        clearError()
        setStatusMessage('')
        setLastAction('start')
        setIsLoading(true)
        try {
            const response = await fetch(`${API_BASE_URL}/interview/start`, { method: 'POST' })
            if (!response.ok) {
                const apiError = await buildApiError(response)
                throw apiError
            }
            const data = await response.json()
            setSessionId(data.session_id || '')
            setConversation([])
            setDraftText('')
            setCurrentQuestion(data.first_question || DEFAULT_QUESTION)
            setStep('interview')
        } catch (error) {
            if (error?.type) setTypedError(error.type, error.message)
            else setTypedError('network', '인터뷰 시작 요청에 실패했습니다.')
        } finally {
            setIsLoading(false)
        }
    }

    const handleSubmit = async () => {
        const normalizedAnswer = userAnswer.trim()
        if (!normalizedAnswer || isLoading) return

        clearError()
        setStatusMessage('')
        setLastAction('submit')
        setIsLoading(true)
        try {
            const response = await fetch(`${API_BASE_URL}/interview/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: sessionId || null,
                    user_text: normalizedAnswer,
                    conversation_history: conversation,
                }),
            })
            if (!response.ok) {
                const apiError = await buildApiError(response)
                throw apiError
            }

            const data = await response.json()
            if (!data?.ai_text || !data?.next_question) {
                throw { type: 'server', message: '서버 응답 형식이 올바르지 않습니다.' }
            }

            setSessionId(data.session_id || sessionId)
            setConversation((prev) => [
                ...prev,
                { role: 'user', text: normalizedAnswer },
                { role: 'ai', text: data.ai_text },
            ])
            setUserAnswer('')
            setCurrentQuestion(data.next_question)
            if (data.summary_updated) {
                setStatusMessage('대화 요약이 갱신되었습니다.')
            }
        } catch (error) {
            if (error?.type) setTypedError(error.type, error.message)
            else setTypedError('network', '답변 전송에 실패했습니다.')
        } finally {
            setIsLoading(false)
        }
    }

    const handleReadQuestion = async () => {
        clearError()
        try {
            const response = await fetch(`${API_BASE_URL}/interview/tts`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: currentQuestion }),
            })
            if (!response.ok) {
                const apiError = await buildApiError(response)
                throw apiError
            }
            const data = await response.json()
            const audio = new Audio(`${API_BASE_URL}${data.audio_url}`)
            await audio.play()
        } catch (error) {
            if (error?.type) setTypedError(error.type, error.message)
            else setTypedError('request', '질문 음성 재생에 실패했습니다.')
        }
    }

    const handleGenerateDraft = async () => {
        if (!sessionId || isDraftLoading) return
        clearError()
        setStatusMessage('')
        setIsDraftLoading(true)
        try {
            const response = await fetch(`${API_BASE_URL}/interview/draft`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sessionId }),
            })
            if (!response.ok) {
                const apiError = await buildApiError(response)
                throw apiError
            }
            const data = await response.json()
            setDraftText(data.draft || '')
            setStatusMessage('자서전 초안을 생성했습니다.')
        } catch (error) {
            if (error?.type) setTypedError(error.type, error.message)
            else setTypedError('request', '초안 생성에 실패했습니다.')
        } finally {
            setIsDraftLoading(false)
        }
    }

    const handleRetry = async () => {
        if (isLoading || isTranscribing) return
        if (lastAction === 'start') return handleStart()
        if (lastAction === 'submit') return handleSubmit()
    }

    const handleTextareaKeyDown = (event) => {
        if (event.key !== 'Enter' || event.shiftKey) return
        event.preventDefault()
        handleSubmit()
    }

    return (
        <div className="story-app">
            <header className="story-header animate-rise">
                <p className="story-kicker">Oral Memoir Studio</p>
                <h1>Tell Your Story</h1>
                <p>
                    정돈된 인터뷰 흐름으로 기억을 모으고,
                    <br />
                    한 번에 초안까지 생성하세요.
                </p>
            </header>

            <main className="story-main">
                {step === 'welcome' && (
                    <Card className="welcome-card animate-rise-delay">
                        <h2>첫 인터뷰를 시작할까요?</h2>
                        <p>
                            대화는 세션으로 저장되고, 질문은 음성으로 들을 수 있습니다.
                            <br />
                            답변이 쌓이면 초안 생성까지 바로 이어집니다.
                        </p>
                        <div className="welcome-actions">
                            <Button onClick={handleStart} disabled={isLoading}>
                                {isLoading ? '준비 중...' : '인터뷰 시작'}
                            </Button>
                        </div>
                        {errorState && (
                            <div className="feedback error-box">
                                <p>{errorState.message}</p>
                                <Button onClick={handleRetry} disabled={isLoading} className="is-ghost">
                                    다시 시도
                                </Button>
                            </div>
                        )}
                    </Card>
                )}

                {step === 'interview' && (
                    <div className="interview-layout">
                        <Card className="interview-card animate-rise">
                            <div className="question-block">
                                <p className="session-label">Session: {sessionId || 'N/A'}</p>
                                <h2>{currentQuestion}</h2>
                                <Button onClick={handleReadQuestion} className="is-ghost">
                                    질문 음성 듣기
                                </Button>
                            </div>

                            {statusMessage && <p className="feedback status-box">{statusMessage}</p>}

                            {errorState && (
                                <div className="feedback error-box">
                                    <p>{errorState.message}</p>
                                    <Button
                                        onClick={handleRetry}
                                        disabled={isLoading || isTranscribing}
                                        className="is-ghost"
                                    >
                                        다시 시도
                                    </Button>
                                </div>
                            )}

                            <section className="history-section">
                                <div className="section-head">
                                    <h3>Conversation</h3>
                                    <span>{conversation.length} messages</span>
                                </div>
                                {conversation.length === 0 ? (
                                    <p className="empty-text">아직 대화 기록이 없습니다.</p>
                                ) : (
                                    <div ref={historyContainerRef} className="history-list">
                                        {conversation.map((message, index) => {
                                            const isUser = message.role === 'user'
                                            return (
                                                <article
                                                    key={`${message.role}-${index}`}
                                                    className={`msg-row ${isUser ? 'is-user' : 'is-ai'}`}
                                                >
                                                    <p className="msg-author">{isUser ? '나' : 'AI 작가'}</p>
                                                    <p className="msg-text">{message.text}</p>
                                                </article>
                                            )
                                        })}
                                    </div>
                                )}
                            </section>

                            <section className="composer-block">
                                <textarea
                                    className="story-textarea"
                                    rows="4"
                                    placeholder={isTranscribing ? '음성 인식 중...' : '답변을 입력해주세요...'}
                                    value={userAnswer}
                                    onChange={(e) => setUserAnswer(e.target.value)}
                                    onKeyDown={handleTextareaKeyDown}
                                    disabled={isLoading || isTranscribing}
                                />
                                <div className="composer-row">
                                    <p>Enter 전송, Shift+Enter 줄바꿈</p>
                                    <Button
                                        onClick={handleSubmit}
                                        disabled={!userAnswer.trim() || isLoading || isTranscribing}
                                    >
                                        {isLoading ? '생성 중...' : '답변 전송'}
                                    </Button>
                                </div>

                                <div className="voice-block">
                                    <p>{isTranscribing ? '음성 인식 처리 중입니다...' : '마이크로 답변을 입력할 수 있습니다.'}</p>
                                    <Microphone
                                        onStart={handleStartRecording}
                                        onStop={handleStopRecording}
                                        isRecording={isRecording}
                                    />
                                </div>
                            </section>
                        </Card>

                        <Card className="draft-card animate-rise-delay">
                            <div className="draft-head">
                                <h3>Autobiography Draft</h3>
                                <Button
                                    onClick={handleGenerateDraft}
                                    disabled={!sessionId || isDraftLoading}
                                    className="is-dark"
                                >
                                    {isDraftLoading ? '생성 중...' : '초안 생성'}
                                </Button>
                            </div>
                            {draftText ? (
                                <pre className="draft-text">{draftText}</pre>
                            ) : (
                                <p className="empty-text">아직 생성된 초안이 없습니다.</p>
                            )}
                        </Card>
                    </div>
                )}
            </main>
        </div>
    )
}

export default App
