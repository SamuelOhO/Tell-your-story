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
    const [step, setStep] = useState('welcome') // welcome, interview
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
            if (error?.type) {
                setTypedError(error.type, error.message)
            } else {
                setTypedError('network', '음성 인식 요청에 실패했습니다.')
            }
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
                if (blob.size > 0) {
                    await uploadRecordingBlob(blob)
                }
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

            <main className="w-full max-w-3xl">
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
                        {errorState && (
                            <div className="space-y-3 rounded-lg bg-rose-50 px-4 py-3 text-base text-rose-700">
                                <p>{errorState.message}</p>
                                <Button onClick={handleRetry} className="px-5 py-2 text-base" disabled={isLoading}>
                                    다시 시도
                                </Button>
                            </div>
                        )}
                    </Card>
                )}

                {step === 'interview' && (
                    <div className="space-y-6">
                        <Card className="space-y-6">
                            <div className="space-y-2 text-center">
                                <h2 className="text-2xl font-semibold text-slate-800">질문</h2>
                                <p className="text-sm text-slate-500">세션 ID: {sessionId || '없음'}</p>
                                <p className="text-2xl md:text-3xl text-slate-900 font-medium leading-relaxed">
                                    &quot;{currentQuestion}&quot;
                                </p>
                                <div className="pt-2">
                                    <Button onClick={handleReadQuestion} className="px-4 py-2 text-base">
                                        질문 음성 듣기
                                    </Button>
                                </div>
                            </div>

                            {statusMessage && (
                                <p className="rounded-lg bg-emerald-50 px-4 py-3 text-base text-emerald-700">{statusMessage}</p>
                            )}

                            {errorState && (
                                <div className="space-y-3 rounded-lg bg-rose-50 px-4 py-3 text-base text-rose-700">
                                    <p>{errorState.message}</p>
                                    <Button onClick={handleRetry} className="px-5 py-2 text-base" disabled={isLoading || isTranscribing}>
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
                                    placeholder={isTranscribing ? '음성 인식 중...' : '답변을 입력해주세요...'}
                                    value={userAnswer}
                                    onChange={(e) => setUserAnswer(e.target.value)}
                                    onKeyDown={handleTextareaKeyDown}
                                    disabled={isLoading || isTranscribing}
                                />
                                <div className="flex flex-wrap items-center justify-between gap-4">
                                    <p className="text-sm text-slate-500">Enter 전송, Shift+Enter 줄바꿈</p>
                                    <Button onClick={handleSubmit} disabled={!userAnswer.trim() || isLoading || isTranscribing}>
                                        {isLoading ? '생각 중...' : '답변하기'}
                                    </Button>
                                </div>

                                <div className="flex flex-col items-center gap-3 rounded-xl border border-slate-200 p-4">
                                    <p className="text-sm text-slate-600">
                                        {isTranscribing ? '음성 인식 처리 중입니다...' : '마이크로 답변을 입력할 수 있습니다.'}
                                    </p>
                                    <Microphone
                                        onStart={handleStartRecording}
                                        onStop={handleStopRecording}
                                        isRecording={isRecording}
                                    />
                                </div>
                            </div>
                        </Card>

                        <Card className="space-y-4">
                            <div className="flex items-center justify-between">
                                <h3 className="text-xl font-semibold text-slate-800">자서전 초안</h3>
                                <Button
                                    onClick={handleGenerateDraft}
                                    className="px-4 py-2 text-base"
                                    disabled={!sessionId || isDraftLoading}
                                >
                                    {isDraftLoading ? '생성 중...' : '초안 생성'}
                                </Button>
                            </div>
                            {draftText ? (
                                <pre className="whitespace-pre-wrap rounded-xl bg-slate-50 p-4 text-base text-slate-700">
                                    {draftText}
                                </pre>
                            ) : (
                                <p className="text-slate-500">아직 생성된 초안이 없습니다.</p>
                            )}
                        </Card>
                    </div>
                )}
            </main>
        </div>
    )
}

export default App
