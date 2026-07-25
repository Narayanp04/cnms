import { useState, useEffect, useRef, useCallback } from 'react'
import { useAuth } from '../context/AuthContext'
import {
  HiOutlineEye, HiOutlineEyeOff,
  HiOutlineUser, HiOutlineLockClosed,
  HiOutlineShieldCheck
} from 'react-icons/hi'
import { FaMicrosoft, FaGoogle, FaNetworkWired, FaServer, FaCloud, FaWifi } from 'react-icons/fa'
import { RiRadarLine } from 'react-icons/ri'

/* ===================================================================
   Canvas Network Background — animated glowing nodes & connecting lines
   =================================================================== */
function NetworkCanvas() {
  const canvasRef = useRef(null)
  const mouseRef = useRef({ x: null, y: null })
  const animRef = useRef(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    let w, h

    function resize() {
      w = canvas.width = window.innerWidth
      h = canvas.height = window.innerHeight
    }
    resize()
    window.addEventListener('resize', resize)

    // Track mouse via event listener directly, not props
    const onMouse = (e) => { mouseRef.current = { x: e.clientX, y: e.clientY } }
    window.addEventListener('mousemove', onMouse)

    const count = 70
    const nodes = []
    for (let i = 0; i < count; i++) {
      nodes.push({
        x: Math.random() * w,
        y: Math.random() * h,
        vx: (Math.random() - 0.5) * 0.35,
        vy: (Math.random() - 0.5) * 0.35,
        r: Math.random() * 2 + 1.2,
        pulse: Math.random() * Math.PI * 2,
        pulseSpeed: 0.005 + Math.random() * 0.01,
      })
    }

    function draw() {
      ctx.clearRect(0, 0, w, h)
      for (const n of nodes) {
        n.x += n.vx; n.y += n.vy
        if (n.x < 0 || n.x > w) n.vx *= -1
        if (n.y < 0 || n.y > h) n.vy *= -1
        n.pulse += n.pulseSpeed
        const glow = 0.5 + Math.sin(n.pulse) * 0.3
        ctx.beginPath()
        ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2)
        ctx.fillStyle = `rgba(0, 229, 255, ${0.4 + glow * 0.5})`
        ctx.shadowColor = '#00E5FF'
        ctx.shadowBlur = 12
        ctx.fill()
        ctx.shadowBlur = 0
      }
      const maxDist = 160
      const mouseInfluence = 200
      const m = mouseRef.current
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const a = nodes[i]; const b = nodes[j]
          const dx = a.x - b.x; const dy = a.y - b.y
          const dist = Math.sqrt(dx * dx + dy * dy)
          if (dist < maxDist) {
            const alpha = (1 - dist / maxDist) * 0.35
            ctx.beginPath()
            ctx.moveTo(a.x, a.y)
            ctx.lineTo(b.x, b.y)
            ctx.strokeStyle = `rgba(0, 229, 255, ${alpha})`
            ctx.lineWidth = 0.6
            ctx.stroke()
          }
        }
        if (m.x !== null && m.y !== null) {
          const dx = a.x - m.x; const dy = a.y - m.y
          const dist = Math.sqrt(dx * dx + dy * dy)
          if (dist < mouseInfluence) {
            const alpha = (1 - dist / mouseInfluence) * 0.25
            ctx.beginPath()
            ctx.moveTo(a.x, a.y); ctx.lineTo(m.x, m.y)
            ctx.strokeStyle = `rgba(0, 184, 255, ${alpha})`
            ctx.lineWidth = 0.8
            ctx.stroke()
          }
        }
      }
      animRef.current = requestAnimationFrame(draw)
    }
    draw()
    return () => {
      window.removeEventListener('resize', resize)
      window.removeEventListener('mousemove', onMouse)
      if (animRef.current) cancelAnimationFrame(animRef.current)
    }
  }, []) // empty deps — never recreates
  return <canvas ref={canvasRef} className="absolute inset-0 z-0" style={{ pointerEvents: 'none' }} />
}

function Particles() {
  const ref = useRef(null)
  useEffect(() => {
    const el = ref.current; if (!el) return
    const f = document.createDocumentFragment()
    for (let i = 0; i < 30; i++) {
      const d = document.createElement('div')
      d.className = 'absolute rounded-full'
      d.style.cssText = `width:${2+Math.random()*4}px;height:${2+Math.random()*4}px;background:rgba(0,229,255,${0.1+Math.random()*0.2});left:${Math.random()*100}%;top:${100+Math.random()*20}%;animation:floatUp ${8+Math.random()*12}s linear infinite;animation-delay:${Math.random()*10}s;opacity:${0.3+Math.random()*0.3}`
      f.appendChild(d)
    }
    el.appendChild(f)
    return () => { el.innerHTML = '' }
  }, [])
  return <div ref={ref} className="absolute inset-0 z-0 pointer-events-none overflow-hidden" />
}

function PulseRings() {
  return (
    <div className="absolute inset-0 z-0 pointer-events-none overflow-hidden flex items-center justify-center">
      {[0, 1, 2].map(i => (
        <div key={i} className="absolute rounded-full border border-cyan-400/10"
          style={{ width: `${200+i*180}px`, height: `${200+i*180}px`, animation: `pulseRing ${4+i*1.5}s ease-in-out infinite`, animationDelay: `${i*1.2}s` }} />
      ))}
    </div>
  )
}

function AnimatedGlobe() {
  return (
    <div className="relative w-28 h-28 mx-auto mb-6">
      <svg viewBox="0 0 120 120" className="w-full h-full">
        <defs><radialGradient id="g" cx="40%" cy="35%"><stop offset="0%" stopColor="#00E5FF" stopOpacity="0.3"/><stop offset="100%" stopColor="#00B8FF" stopOpacity="0.05"/></radialGradient></defs>
        <circle cx="60" cy="60" r="54" fill="url(#g)" stroke="#00E5FF" strokeWidth="0.8" opacity="0.5"/>
        <ellipse cx="60" cy="60" rx="40" ry="12" fill="none" stroke="#00E5FF" strokeWidth="0.4" opacity="0.15"/>
        <ellipse cx="60" cy="60" rx="20" ry="6" fill="none" stroke="#00E5FF" strokeWidth="0.4" opacity="0.1"/>
        <line x1="20" y1="60" x2="100" y2="60" stroke="#00E5FF" strokeWidth="0.4" opacity="0.15"/>
        <path d="M30 45 Q60 85 90 50" fill="none" stroke="#00E5FF" strokeWidth="1.2" opacity="0.35" strokeDasharray="4 4" className="animate-[dashMove_3s_linear_infinite]"/>
        <path d="M25 70 Q60 30 95 65" fill="none" stroke="#4FC3F7" strokeWidth="0.8" opacity="0.2" strokeDasharray="3 5" className="animate-[dashMove_4s_linear_infinite]"/>
        {[{cx:42,cy:52,r:2,op:0.6,d:2},{cx:70,cy:48,r:1.5,op:0.5,d:2.5},{cx:55,cy:72,r:1.8,op:0.5,d:3},{cx:78,cy:65,r:1.2,op:0.4,d:1.8}].map((n,i) => (
          <circle key={i} cx={n.cx} cy={n.cy} r={n.r} fill="#00E5FF" opacity={n.op}><animate attributeName="opacity" values="0.3;1;0.3" dur={`${n.d}s`} repeatCount="indefinite"/></circle>
        ))}
      </svg>
      <div className="absolute inset-0 flex items-center justify-center"><div className="w-24 h-24 border border-cyan-400/10 rounded-full animate-[spin_8s_linear_infinite]"/></div>
    </div>
  )
}

function NetworkTopology() {
  const icons = [
    { Icon: FaNetworkWired, label: 'Router', x: '15%', y: '20%', delay: 0 },
    { Icon: HiOutlineShieldCheck, label: 'Firewall', x: '35%', y: '15%', delay: 0.3 },
    { Icon: FaServer, label: 'Server', x: '55%', y: '25%', delay: 0.6 },
    { Icon: FaCloud, label: 'Cloud', x: '75%', y: '18%', delay: 0.9 },
    { Icon: FaWifi, label: 'Wi-Fi', x: '90%', y: '30%', delay: 1.2 },
  ]
  return (
    <div className="relative w-full max-w-lg mx-auto mb-8" style={{ height: '160px' }}>
      <svg className="absolute inset-0 w-full h-full z-0" style={{ opacity: 0.25 }}>
        {[['15%','20%','35%','15%','#00E5FF',2],['35%','15%','55%','25%','#00B8FF',2.5],['55%','25%','75%','18%','#4FC3F7',2],['75%','18%','90%','30%','#00E5FF',3]].map(([x1,y1,x2,y2,c,d],i) => (
          <line key={i} x1={x1} y1={y1} x2={x2} y2={y2} stroke={c} strokeWidth="1" strokeDasharray="4 3"><animate attributeName="stroke-dashoffset" values="0;-20" dur={`${d}s`} repeatCount="indefinite"/></line>
        ))}
      </svg>
      {icons.map(({Icon,label,x,y,delay},i) => (
        <div key={i} className="absolute z-10 flex flex-col items-center gap-1 animate-fadeInUp" style={{left:x,top:y,animationDelay:`${delay}s`,animationFillMode:'both'}}>
          <div className="w-10 h-10 rounded-full bg-white/5 border border-cyan-400/20 flex items-center justify-center backdrop-blur-sm group hover:border-cyan-400/50 hover:bg-white/10 transition-all duration-300 hover:shadow-[0_0_20px_rgba(0,229,255,0.3)]">
            <Icon className="text-cyan-400 text-lg group-hover:text-cyan-300 transition-colors" />
          </div>
          <span className="text-[10px] text-cyan-300/60 font-mono tracking-wider">{label}</span>
        </div>
      ))}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-10">
        <div className="w-3 h-3 rounded-full bg-cyan-400 shadow-[0_0_20px_rgba(0,229,255,0.6)] animate-ping opacity-30" />
        <div className="w-2 h-2 rounded-full bg-cyan-400 absolute top-0.5 left-0.5" />
      </div>
    </div>
  )
}

export default function LoginPage() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [rememberMe, setRememberMe] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const { login } = useAuth()

  // Refs for direct DOM parallax (no React re-renders)
  const parallaxLeftRef = useRef(null)
  const parallaxRightRef = useRef(null)

  const handleMouseMove = useCallback((e) => {
    const cx = window.innerWidth / 2, cy = window.innerHeight / 2
    const x = (e.clientX - cx) / cx
    const y = (e.clientY - cy) / cy
    if (parallaxLeftRef.current)
      parallaxLeftRef.current.style.transform = `translate(${x * -8}px, ${y * -8}px)`
    if (parallaxRightRef.current)
      parallaxRightRef.current.style.transform = `translate(${x * 5}px, ${y * 5}px)`
  }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    if (!username || !password) { setError('Please enter your credentials'); return }
    setLoading(true)
    try {
      if (rememberMe) localStorage.setItem('rememberedUser', username)
      else localStorage.removeItem('rememberedUser')
      await login(username, password)
    } catch (err) {
      setError(err.response?.data?.detail || 'Authentication failed. Please try again.')
    } finally { setLoading(false) }
  }

  useEffect(() => {
    const saved = localStorage.getItem('rememberedUser')
    if (saved) { setUsername(saved); setRememberMe(true) }
  }, [])

  return (
    <div className="relative min-h-screen overflow-hidden" onMouseMove={handleMouseMove}
      style={{ background: 'radial-gradient(ellipse at 50% 0%, #071A35 0%, #050B18 50%, #020812 100%)' }}>
      <NetworkCanvas />
      <Particles />
      <div className="absolute top-[-300px] left-1/2 -translate-x-1/2 w-[600px] h-[600px] rounded-full bg-cyan-500/5 blur-[100px] pointer-events-none" />
      <div className="absolute bottom-[-200px] right-[-200px] w-[400px] h-[400px] rounded-full bg-blue-500/5 blur-[80px] pointer-events-none" />

      <div className="relative z-10 min-h-screen flex flex-col lg:flex-row">
        {/* LEFT — Branding */}
        <div className="flex-1 flex flex-col items-center justify-center p-8 lg:p-16 relative">
          <div ref={parallaxLeftRef} className="max-w-xl w-full">
            <div className="flex items-center gap-3 mb-4 animate-fadeInUp" style={{ animationDelay: '0.1s' }}>
              <div className="relative w-12 h-12 rounded-2xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-[0_0_30px_rgba(0,229,255,0.3)]">
                <span className="text-white font-black text-xl tracking-tight">CX</span>
                <div className="absolute -inset-1 rounded-2xl border border-cyan-400/20 animate-pulse opacity-50" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white tracking-tight">ConnectXperts</h1>
                <p className="text-xs text-cyan-300/70 font-mono tracking-widest uppercase">Network Management Suite</p>
              </div>
            </div>
            <h2 className="text-4xl md:text-5xl lg:text-6xl font-extrabold text-white leading-tight mt-6 animate-fadeInUp" style={{ animationDelay: '0.2s' }}>
              Welcome to<br />
              <span className="bg-gradient-to-r from-cyan-400 via-cyan-300 to-blue-400 bg-clip-text text-transparent">ConnectXperts</span>
            </h2>
            <p className="text-base md:text-lg text-gray-400 mt-4 max-w-lg leading-relaxed animate-fadeInUp" style={{ animationDelay: '0.3s' }}>
              Secure Network Infrastructure · Monitoring · Cloud · Cybersecurity
            </p>
            <div className="flex flex-wrap gap-2 mt-6 animate-fadeInUp" style={{ animationDelay: '0.4s' }}>
              {['NOC Ready','99.99% Uptime','Real-time','AI Driven','SOC 2'].map(t => (
                <span key={t} className="px-3 py-1 text-xs font-medium rounded-full border border-cyan-500/20 text-cyan-300/80 bg-cyan-500/5 backdrop-blur-sm">{t}</span>
              ))}
            </div>
            <div className="mt-8 animate-fadeInUp" style={{ animationDelay: '0.5s' }}><NetworkTopology /></div>
            <div className="grid grid-cols-3 gap-4 mt-6 animate-fadeInUp" style={{ animationDelay: '0.6s' }}>
              {[{v:'10K+',l:'Devices'},{v:'99.99%',l:'Uptime SLA'},{v:'<5ms',l:'Avg Latency'}].map(s => (
                <div key={s.l} className="text-center p-3 rounded-xl bg-white/[0.03] border border-white/[0.06] backdrop-blur-sm">
                  <div className="text-lg md:text-xl font-bold text-white">{s.v}</div>
                  <div className="text-[10px] text-gray-500 uppercase tracking-wider mt-0.5">{s.l}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* RIGHT — Login Card */}
        <div className="flex-1 flex items-center justify-center p-6 lg:p-16 relative">
          <PulseRings />
          <div ref={parallaxRightRef} className="relative w-full max-w-md">
            <div className="relative rounded-2xl p-8 md:p-10 border border-white/[0.08]"
              style={{ background: 'linear-gradient(135deg, rgba(255,255,255,0.06) 0%, rgba(255,255,255,0.02) 100%)', backdropFilter: 'blur(24px)', WebkitBackdropFilter: 'blur(24px)', boxShadow: '0 8px 32px rgba(0,0,0,0.4), 0 0 80px rgba(0,229,255,0.05), inset 0 1px 0 rgba(255,255,255,0.08)' }}>
              <div className="absolute top-0 left-8 right-8 h-px bg-gradient-to-r from-transparent via-cyan-400/40 to-transparent" />
              <div className="text-center mb-6">
                <AnimatedGlobe />
                <h2 className="text-xl font-bold text-white mt-2">Welcome Back</h2>
                <p className="text-sm text-gray-400 mt-1">Sign in to your account</p>
              </div>
              {error && (
                <div className="mb-5 p-3 rounded-xl border border-red-500/20 bg-red-500/10 backdrop-blur-sm text-sm text-red-300 flex items-start gap-2.5 animate-shake">
                  <HiOutlineShieldCheck className="w-4 h-4 mt-0.5 flex-shrink-0 text-red-400" /><span>{error}</span>
                </div>
              )}
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="group">
                  <label className="block text-xs font-medium text-gray-300 mb-1.5 ml-1 tracking-wide uppercase">Username</label>
                  <div className="relative">
                    <HiOutlineUser className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500 group-focus-within:text-cyan-400 transition-colors duration-300" />
                    <input type="text" value={username} onChange={e => setUsername(e.target.value)}
                      className="w-full pl-10 pr-4 py-3 rounded-xl text-sm text-white bg-white/[0.04] border border-white/[0.1] placeholder:text-gray-600 focus:outline-none focus:border-cyan-500/50 focus:bg-white/[0.06] transition-all duration-300"
                      placeholder="Enter your username" autoComplete="username" autoFocus
                      style={{ boxShadow: username ? '0 0 0 1px rgba(0,229,255,0.1)' : 'none' }} />
                    <div className="absolute inset-0 rounded-xl pointer-events-none opacity-0 group-focus-within:opacity-100 transition-opacity duration-500"
                      style={{ boxShadow: '0 0 20px rgba(0,229,255,0.08)', border: '1px solid rgba(0,229,255,0.15)' }} />
                  </div>
                </div>
                <div className="group">
                  <label className="block text-xs font-medium text-gray-300 mb-1.5 ml-1 tracking-wide uppercase">Password</label>
                  <div className="relative">
                    <HiOutlineLockClosed className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500 group-focus-within:text-cyan-400 transition-colors duration-300" />
                    <input type={showPassword?'text':'password'} value={password} onChange={e => setPassword(e.target.value)}
                      className="w-full pl-10 pr-12 py-3 rounded-xl text-sm text-white bg-white/[0.04] border border-white/[0.1] placeholder:text-gray-600 focus:outline-none focus:border-cyan-500/50 focus:bg-white/[0.06] transition-all duration-300"
                      placeholder="Enter your password" autoComplete="current-password" />
                    <button type="button" onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3.5 top-1/2 -translate-y-1/2 text-gray-500 hover:text-cyan-400 transition-colors" tabIndex={-1}>
                      {showPassword ? <HiOutlineEyeOff className="w-4 h-4" /> : <HiOutlineEye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <label className="relative flex items-center gap-2 cursor-pointer group">
                    <input type="checkbox" id="remember-me" checked={rememberMe} onChange={e => setRememberMe(e.target.checked)}
                      className="w-4 h-4 rounded border-gray-600 bg-white/5 cursor-pointer appearance-none checked:bg-cyan-500/20 checked:border-cyan-400/50 transition-all duration-200"
                      style={{ border: '1px solid rgba(255,255,255,0.15)', boxShadow: rememberMe ? '0 0 10px rgba(0,229,255,0.2)' : 'none' }} />
                    {rememberMe && <svg className="absolute left-0 w-4 h-4 text-cyan-400 pointer-events-none" viewBox="0 0 24 24" fill="none"><path d="M5 13l4 4L19 7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>}
                    <span className="text-gray-400 group-hover:text-gray-300 transition-colors">Remember me</span>
                  </label>
                  <a href="#" onClick={e => e.preventDefault()} className="text-cyan-400/80 hover:text-cyan-300 transition-colors font-medium">Forgot password?</a>
                </div>
                <button type="submit" disabled={loading}
                  className="relative w-full py-3.5 rounded-xl font-semibold text-sm text-white overflow-hidden transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
                  style={{ background: 'linear-gradient(135deg, #00B8FF 0%, #00E5FF 50%, #4FC3F7 100%)', boxShadow: loading ? '0 0 20px rgba(0,229,255,0.3)' : '0 4px 20px rgba(0,229,255,0.2)' }}
                  onMouseEnter={e => {if(!loading)e.currentTarget.style.boxShadow='0 4px 30px rgba(0,229,255,0.4),0 0 60px rgba(0,229,255,0.1)'}}
                  onMouseLeave={e => {if(!loading)e.currentTarget.style.boxShadow='0 4px 20px rgba(0,229,255,0.2)'}}>
                  <div className="absolute inset-0 bg-[linear-gradient(110deg,transparent_25%,rgba(255,255,255,0.2)_50%,transparent_75%)] animate-[shine_3s_ease-in-out_infinite]" />
                  <span className="relative z-10 flex items-center justify-center gap-2">
                    {loading ? <><svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>Authenticating...</>
                      : <><RiRadarLine className="w-4 h-4" />Sign In to Network</>}
                  </span>
                </button>
              </form>
              <div className="flex items-center gap-3 my-6">
                <div className="flex-1 h-px bg-gradient-to-r from-transparent via-white/[0.08] to-transparent" />
                <span className="text-xs text-gray-500 uppercase tracking-widest">or</span>
                <div className="flex-1 h-px bg-gradient-to-r from-transparent via-white/[0.08] to-transparent" />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <button type="button" className="flex items-center justify-center gap-2.5 py-2.5 px-4 rounded-xl text-xs font-medium text-gray-300 border border-white/[0.08] bg-white/[0.03] hover:bg-white/[0.06] hover:border-white/[0.15] hover:text-white transition-all duration-200 backdrop-blur-sm">
                  <FaMicrosoft className="w-4 h-4 text-blue-400" />Microsoft
                </button>
                <button type="button" className="flex items-center justify-center gap-2.5 py-2.5 px-4 rounded-xl text-xs font-medium text-gray-300 border border-white/[0.08] bg-white/[0.03] hover:bg-white/[0.06] hover:border-white/[0.15] hover:text-white transition-all duration-200 backdrop-blur-sm">
                  <FaGoogle className="w-4 h-4 text-red-400" />Google
                </button>
              </div>
              <div className="mt-6 text-center">
                <p className="text-xs text-gray-500">Default: <span className="text-gray-400 font-mono">admin</span> / <span className="text-gray-400 font-mono">admin123</span></p>
              </div>
            </div>
            <div className="mt-6 text-center text-xs text-gray-600">
              <p>&copy; {new Date().getFullYear()} ConnectXperts. All rights reserved.</p>
              <div className="flex items-center justify-center gap-4 mt-2">
                <a href="#" onClick={e=>e.preventDefault()} className="hover:text-gray-400 transition-colors">Privacy</a><span className="text-gray-700">·</span>
                <a href="#" onClick={e=>e.preventDefault()} className="hover:text-gray-400 transition-colors">Terms</a><span className="text-gray-700">·</span>
                <a href="#" onClick={e=>e.preventDefault()} className="hover:text-gray-400 transition-colors">Security</a>
              </div>
            </div>
          </div>
        </div>
      </div>

      <style>{`
        @keyframes floatUp { 0%{transform:translateY(0) scale(1);opacity:0} 10%{opacity:0.5} 90%{opacity:0.3} 100%{transform:translateY(-110vh) scale(0.5);opacity:0} }
        @keyframes pulseRing { 0%{transform:scale(0.8);opacity:0.3} 50%{opacity:0.08} 100%{transform:scale(1.5);opacity:0} }
        @keyframes dashMove { to{stroke-dashoffset:-20} }
        @keyframes shine { 0%{transform:translateX(-100%)} 50%{transform:translateX(100%)} 100%{transform:translateX(200%)} }
        @keyframes fadeInUp { from{opacity:0;transform:translateY(20px)} to{opacity:1;transform:translateY(0)} }
        @keyframes shake { 0%,100%{transform:translateX(0)} 10%,30%,50%,70%,90%{transform:translateX(-3px)} 20%,40%,60%,80%{transform:translateX(3px)} }
        .animate-fadeInUp { animation:fadeInUp 0.7s ease-out both }
        .animate-shake { animation:shake 0.5s ease-in-out }
      `}</style>
    </div>
  )
}
