import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Home, FileText, Menu, X, LogOut, User, LayoutDashboard, PlusCircle } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function Navbar() {
  const [isOpen, setIsOpen] = React.useState(false);
  const location = useLocation();
  const { user, logout } = useAuth();

  const isActive = (path) => location.pathname === path 
    ? "bg-white/15 text-white" 
    : "text-blue-100 hover:bg-white/10 hover:text-white";

  return (
    <header>
      {/* Main Navy Bar */}
      <nav className="bg-primary-dark">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            {/* Brand / Emblem */}
            <div className="flex items-center">
              <Link to="/" className="flex items-center gap-3">
                {/* Ashoka Chakra emblem */}
                <div className="flex items-center justify-center w-10 h-10 rounded-full bg-white/10 border border-white/20">
                  <span className="text-2xl leading-none text-saffron" aria-hidden="true">&#9784;</span>
                </div>
                <div className="hidden sm:block">
                  <div className="text-white font-bold text-lg tracking-tight leading-tight">
                    जन-सुनवाई
                  </div>
                  <div className="text-blue-200 text-[11px] tracking-wide leading-tight">
                    Public Grievance Redressal System
                  </div>
                </div>
                <div className="sm:hidden">
                  <span className="text-white font-bold text-base">जन-सुनवाई</span>
                </div>
              </Link>
            </div>
            
            {/* Desktop Nav Links */}
            <div className="hidden md:flex md:items-center md:space-x-1">
              <Link to="/" className={`px-3 py-2 rounded text-sm font-medium transition ${isActive('/')}`}>
                <Home className="inline-block w-4 h-4 mr-1 -mt-0.5" />
                Home
              </Link>
              {user && (
                <>
                  <Link to="/dashboard" className={`px-3 py-2 rounded text-sm font-medium transition ${isActive('/dashboard')}`}>
                    <LayoutDashboard className="inline-block w-4 h-4 mr-1 -mt-0.5" />
                    Dashboard
                  </Link>
                  <Link to="/analyze" className={`px-3 py-2 rounded text-sm font-medium transition ${isActive('/analyze')}`}>
                    <PlusCircle className="inline-block w-4 h-4 mr-1 -mt-0.5" />
                    File Complaint
                  </Link>
                </>
              )}

              <div className="h-6 w-px bg-white/20 mx-2"></div>

              {user ? (
                <div className="flex items-center space-x-3">
                  <div className="flex items-center text-blue-100 text-sm">
                    <User className="w-4 h-4 mr-1.5" />
                    <span className="font-medium">{user.username}</span>
                    <span className="ml-2 text-[10px] px-2 py-0.5 rounded-sm bg-saffron/90 text-white font-semibold uppercase tracking-wider">
                      {user.role === 'dept_head' ? 'Dept Head' : user.role === 'admin' ? 'Admin' : 'Citizen'}
                    </span>
                  </div>
                  <button 
                    onClick={logout} 
                    className="text-blue-200 hover:text-white transition p-1.5 rounded hover:bg-white/10" 
                    title="Logout"
                  >
                    <LogOut className="w-4 h-4" />
                  </button>
                </div>
              ) : (
                <div className="flex items-center space-x-2">
                  <Link to="/login" className="px-3 py-1.5 rounded text-sm font-medium text-blue-100 hover:text-white hover:bg-white/10 transition">
                    Log In
                  </Link>
                  <Link to="/register" className="bg-saffron text-white px-4 py-1.5 rounded text-sm font-semibold hover:bg-saffron-light transition">
                    Register
                  </Link>
                </div>
              )}
            </div>

            {/* Mobile menu button */}
            <div className="-mr-2 flex items-center md:hidden">
              <button
                onClick={() => setIsOpen(!isOpen)}
                className="inline-flex items-center justify-center p-2 rounded text-blue-200 hover:text-white hover:bg-white/10 focus:outline-none"
              >
                {isOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Tricolor Stripe */}
      <div className="tricolor-bar" aria-hidden="true"></div>

      {/* Mobile Menu */}
      {isOpen && (
        <div className="md:hidden bg-primary border-t border-white/10">
          <div className="px-4 pt-2 pb-3 space-y-1">
            <Link 
              to="/" 
              onClick={() => setIsOpen(false)}
              className="block px-3 py-2.5 rounded text-base font-medium text-blue-100 hover:text-white hover:bg-white/10"
            >
              Home
            </Link>
            {user && (
              <>
                <Link 
                  to="/dashboard" 
                  onClick={() => setIsOpen(false)}
                  className="block px-3 py-2.5 rounded text-base font-medium text-blue-100 hover:text-white hover:bg-white/10"
                >
                  Dashboard
                </Link>
                <Link 
                  to="/analyze" 
                  onClick={() => setIsOpen(false)}
                  className="block px-3 py-2.5 rounded text-base font-medium text-blue-100 hover:text-white hover:bg-white/10"
                >
                  File Complaint
                </Link>
              </>
            )}
            <div className="border-t border-white/10 my-2"></div>
            {user ? (
              <div className="px-3 py-2 flex items-center justify-between">
                <span className="text-blue-100 text-sm flex items-center">
                  <User className="w-4 h-4 mr-2" />
                  {user.username}
                  <span className="ml-2 text-[10px] px-2 py-0.5 rounded-sm bg-saffron/90 text-white font-semibold uppercase">
                    {user.role === 'dept_head' ? 'Dept Head' : user.role === 'admin' ? 'Admin' : 'Citizen'}
                  </span>
                </span>
                <button onClick={logout} className="text-blue-200 hover:text-white p-1.5">
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <div className="flex flex-col gap-2 px-3">
                <Link to="/login" onClick={() => setIsOpen(false)} className="block py-2 text-center rounded text-blue-100 hover:text-white hover:bg-white/10 font-medium">
                  Log In
                </Link>
                <Link to="/register" onClick={() => setIsOpen(false)} className="block py-2 text-center rounded bg-saffron text-white font-semibold hover:bg-saffron-light">
                  Register
                </Link>
              </div>
            )}
          </div>
        </div>
      )}
    </header>
  );
}
