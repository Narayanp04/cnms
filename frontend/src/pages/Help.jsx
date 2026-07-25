import { HiOutlineBookOpen, HiOutlineQuestionMarkCircle, HiOutlineMail, HiOutlineTerminal } from 'react-icons/hi'

export default function Help() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Help & Documentation</h1>
        <p className="text-sm text-gray-500">User manual and quick start guide</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card p-6">
          <HiOutlineBookOpen className="w-8 h-8 text-primary-600 mb-3" />
          <h3 className="text-lg font-semibold mb-2">Quick Start Guide</h3>
          <ol className="space-y-3 text-sm text-gray-600 dark:text-gray-400">
            <li>1. <strong>Add Devices</strong> - Go to Devices &gt; Add Device to start monitoring</li>
            <li>2. <strong>Configure Alerts</strong> - Set up WhatsApp, Email, or Telegram notifications</li>
            <li>3. <strong>View Dashboard</strong> - Monitor real-time status on the dashboard</li>
            <li>4. <strong>Generate Reports</strong> - Create SLA reports and export as PDF/Excel</li>
            <li>5. <strong>AI Analysis</strong> - Use AI to detect patterns and predict failures</li>
          </ol>
        </div>

        <div className="card p-6">
          <HiOutlineQuestionMarkCircle className="w-8 h-8 text-primary-600 mb-3" />
          <h3 className="text-lg font-semibold mb-2">FAQ</h3>
          <div className="space-y-3 text-sm text-gray-600 dark:text-gray-400">
            <div>
              <p className="font-medium text-gray-900 dark:text-white">How do I bulk import devices?</p>
              <p>Go to Devices, click Bulk Import, and upload a CSV file with the required columns.</p>
            </div>
            <div>
              <p className="font-medium text-gray-900 dark:text-white">How to set up WhatsApp alerts?</p>
              <p>Go to Settings &gt; Notifications and configure WhatsApp Cloud API credentials.</p>
            </div>
            <div>
              <p className="font-medium text-gray-900 dark:text-white">How does AI analysis work?</p>
              <p>AI analyzes 14 days of ping history to detect patterns, anomalies, and predict failures.</p>
            </div>
          </div>
        </div>

        <div className="card p-6">
          <HiOutlineTerminal className="w-8 h-8 text-primary-600 mb-3" />
          <h3 className="text-lg font-semibold mb-2">API Documentation</h3>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
            Access the interactive API documentation at:
          </p>
          <a href="/api/docs" target="_blank" className="text-primary-600 hover:text-primary-700 font-medium text-sm">
            /api/docs (Swagger UI)
          </a>
          <br />
          <a href="/api/redoc" target="_blank" className="text-primary-600 hover:text-primary-700 font-medium text-sm">
            /api/redoc (ReDoc)
          </a>
        </div>

        <div className="card p-6">
          <HiOutlineMail className="w-8 h-8 text-primary-600 mb-3" />
          <h3 className="text-lg font-semibold mb-2">Support</h3>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
            For technical support:
          </p>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Email: support@connectxperts.com<br />
            Documentation: docs.connectxperts.com<br />
            GitHub: github.com/connectxperts/nms
          </p>
        </div>
      </div>
    </div>
  )
}
