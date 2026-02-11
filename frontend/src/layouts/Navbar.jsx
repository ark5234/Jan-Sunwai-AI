import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Camera, Home, FileText, Menu, X } from 'lucide-react';

export default function Navbar() {
  const [isOpen, setIsOpen] = React.useState(false);
  const location = useLocation();

  const isActive = (path) => location.pathname === path ? "bg-primary text-white" : "text-slate-600 hover:bg-slate-100";

  return (
    <nav className="bg-white shadow-md border-b border-slate-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex">
            <Link to="/" className="flex-shrink-0 flex items-center">
              <Camera className="h-8 w-8 text-primary" />
              <span className="ml-2 font-bold text-xl tracking-tight text-slate-800">Jan-Sunwai AI</span>
            </Link>
          </div>
          
          <div className="hidden md:ml-6 md:flex md:space-x-8 items-center">
            <Link to="/" className={`px-3 py-2 rounded-md text-sm font-medium ${isActive('/')}`}>
              Home
            </Link>
            <Link to="/analyze" className={`px-3 py-2 rounded-md text-sm font-medium ${isActive('/analyze')}`}>
              New Complaint
            </Link>
            <Link to="/results" className={`px-3 py-2 rounded-md text-sm font-medium ${isActive('/results')}`}>
              Track Status
            </Link>
          </div>

          <div className="-mr-2 flex items-center md:hidden">
            <button
              onClick={() => setIsOpen(!isOpen)}
              className="inline-flex items-center justify-center p-2 rounded-md text-slate-400 hover:text-slate-500 hover:bg-slate-100 focus:outline-none"
            >
              {isOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
            </button>
          </div>
        </div>
      </div>

      {isOpen && (
        <div className="md:hidden">
          <div className="pt-2 pb-3 space-y-1">
            <Link to="/" className="block px-3 py-2 rounded-md text-base font-medium text-slate-700 hover:text-slate-900 hover:bg-slate-50">Home</Link>
            <Link to="/analyze" className="block px-3 py-2 rounded-md text-base font-medium text-slate-700 hover:text-slate-900 hover:bg-slate-50">New Complaint</Link>
          </div>
        </div>
      )}
    </nav>
  );
}
