import { Link, useLocation, useNavigate } from 'react-router-dom';
import { auth } from '../auth';

interface LayoutProps {
  children: React.ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const location = useLocation();
  const navigate = useNavigate();
  const user = auth.getUser();

  const handleLogout = () => {
    auth.logout();
    navigate('/login');
  };

  const currentUser = auth.getUser();

  const navItems = [
    { path: '/', label: 'Dashboard', icon: '📊' },
    { path: '/sites', label: 'Sedi', icon: '🏢' },
    { path: '/suppliers', label: 'Fornitori', icon: '🚚' },
    { path: '/people', label: 'Persone', icon: '👥', color: 'text-blue-500' },
    { path: '/assets', label: 'Asset', icon: '💻' },
    { path: '/inventory', label: 'Magazzino', icon: '📦' },
    { path: '/sims', label: 'SIM', icon: '📱' },
    { path: '/badges', label: 'Badge', icon: '🪪' },
    { path: '/assignments', label: 'Assegnazioni', icon: '📋' },
    { path: '/documents', label: 'Documenti', icon: '📄' },
    { path: '/reports', label: 'Report', icon: '📈' },
    { path: '/settings', label: 'Impostazioni', icon: '⚙️' },
  ];

  return (
    <div className="flex flex-col min-h-screen bg-gray-50">
      <header className="bg-asset-manager-gray text-white px-4 py-3 flex justify-between items-center flex-shrink-0">
        <h1 className="text-xl font-semibold m-0">IT Asset Manager</h1>
        {user && (
          <div className="flex items-center gap-4">
            <span className="text-sm">{user.username}</span>
            <button 
              onClick={handleLogout}
              className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors text-sm"
            >
              Logout
            </button>
          </div>
        )}
      </header>
      <nav className="bg-asset-manager-gray-hover flex gap-0 overflow-x-auto flex-shrink-0">
        {navItems.map((item) => (
          <Link
            key={item.path}
            to={item.path}
            className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
              location.pathname === item.path
                ? 'bg-asset-manager-yellow text-asset-manager-gray'
                : 'text-gray-300 hover:bg-gray-700'
            }`}
          >
            <span className={`text-xl ${item.color || ''}`}>{item.icon}</span>
            <span className="font-medium">{item.label}</span>
          </Link>
        ))}
      </nav>
      <main className="flex-1 overflow-y-auto">
        <div className="w-full mx-auto px-2 py-6">
          {children}
        </div>
      </main>
    </div>
  );
}

