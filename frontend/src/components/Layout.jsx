import { useState } from 'react'
import { Outlet, NavLink, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useTheme } from '../context/ThemeContext'
import { 
  HiOutlineHome, HiOutlineServer, HiOutlineChartBar, HiOutlineBell,
  HiOutlineDocumentText, HiOutlineClock, HiOutlineGlobe, HiOutlineLightBulb,
  HiOutlineMap, HiOutlineUsers, HiOutlineCog, HiOutlineQuestionMarkCircle,
  HiOutlineMenu, HiOutlineX, HiOutlineLogout, HiOutlineSun, HiOutlineMoon,
  HiOutlineShieldCheck, HiOutlineDatabase, HiOutlineMail
} from 'react-icons/hi'

const navItems = [
  { path: '/dashboard', label: 'Dashboard', icon: HiOutlineHome },
  { path: '/devices', label: 'Devices', icon: HiOutlineServer },
  { path: '/monitoring', label: 'Monitoring', icon: HiOutlineChartBar },
  { path: '/alerts', label: 'Alerts', icon: HiOutlineBell },
  { path: '/sla', label: 'SLA Reports', icon: HiOutlineShieldCheck },
  { path: '/reports', label: 'Reports', icon: HiOutlineDocumentText },
  { path: '/events', label: 'Event Logs', icon: HiOutlineClock },
  { path: '/ai', label: 'AI Analytics', icon: HiOutlineLightBulb },
  { path: '/maps', label: 'Maps', icon: HiOutlineMap },
  { path: '/notifications', label: 'Notifications', icon: HiOutlineMail },
  { path: '/customers', label: 'Customers', icon: HiOutlineUsers },
  { path: '/backup', label: 'Backup', icon: HiOutlineDatabase },
  { path: '/settings', label: 'Settings', icon: HiOutlineCog },
  { path: '/help', label: 'Help', icon: HiOutlineQuestionMarkCircle },
]

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const { user, logout } = useAuth()
  const { darkMode, toggleTheme } = useTheme()
  const location = useLocation()

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50 dark:bg-gray-900">
      {/* Sidebar overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside className={`
        fixed lg:static inset-y-0 left-0 z-50 w-64 bg-white dark:bg-gray-800 
        border-r border-gray-200 dark:border-gray-700 
        transform transition-transform duration-300 ease-in-out
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        flex flex-col
      `}>
        {/* Logo */}
        <div className="flex items-center justify-between h-16 px-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-gradient-to-br from-primary-500 to-primary-700 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">CN</span>
            </div>
            <div>
              <h1 className="text-lg font-bold text-gray-900 dark:text-white">ConnectXperts</h1>
              <p className="text-xs text-gray-500 dark:text-gray-400">NMS Platform</p>
            </div>
          </div>
          <button 
            className="lg:hidden text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
            onClick={() => setSidebarOpen(false)}
          >
            <HiOutlineX className="w-6 h-6" />
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-1 scrollbar-thin">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) => `
                sidebar-link ${isActive ? 'sidebar-link-active' : ''}
              `}
            >
              <item.icon className="w-5 h-5 flex-shrink-0" />
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>

        {/* Bottom section */}
        <div className="p-4 border-t border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-primary-100 dark:bg-primary-900/50 rounded-full flex items-center justify-center">
                <span className="text-primary-700 dark:text-primary-400 font-semibold text-sm">
                  {user?.full_name?.charAt(0)?.toUpperCase() || user?.username?.charAt(0)?.toUpperCase()}
                </span>
              </div>
              <div className="text-sm">
                <p className="font-medium text-gray-900 dark:text-white truncate max-w-[120px]">
                  {user?.full_name || user?.username}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400 capitalize">{user?.role}</p>
              </div>
            </div>
            <button
              onClick={logout}
              className="p-2 text-gray-500 hover:text-danger-600 transition-colors rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
              title="Logout"
            >
              <HiOutlineLogout className="w-5 h-5" />
            </button>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="h-16 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between px-4 lg:px-6">
          <div className="flex items-center gap-3">
            <button 
              className="lg:hidden text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
              onClick={() => setSidebarOpen(true)}
            >
              <HiOutlineMenu className="w-6 h-6" />
            </button>
            <div>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                {navItems.find(i => location.pathname.startsWith(i.path))?.label || 'Dashboard'}
              </h2>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={toggleTheme}
              className="p-2 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              title={darkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
            >
              {darkMode ? <HiOutlineSun className="w-5 h-5" /> : <HiOutlineMoon className="w-5 h-5" />}
            </button>
            
            <NavLink
              to="/alerts"
              className="p-2 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors relative"
              title="Alerts"
            >
              <HiOutlineBell className="w-5 h-5" />
              <span className="absolute -top-1 -right-1 w-4 h-4 bg-danger-500 rounded-full text-white text-xs flex items-center justify-center">
                0
              </span>
            </NavLink>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto p-4 lg:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
