import React from 'react';
import { Link } from 'react-router-dom';
import { Upload, MapPin, FileCheck, Shield, Clock, Building2, ArrowRight, CheckCircle2 } from 'lucide-react';

const CATEGORIES = [
  { name: 'Roads & Potholes', dept: 'Municipal - PWD Roads' },
  { name: 'Street Lighting', dept: 'Municipal - Street Lighting' },
  { name: 'Sanitation & Waste', dept: 'Municipal - Sanitation' },
  { name: 'Water & Sewerage', dept: 'Municipal - Water and Sewerage' },
  { name: 'Power Supply', dept: 'Utility - Power DISCOM' },
  { name: 'Traffic & Safety', dept: 'Police - Traffic' },
  { name: 'Law & Order', dept: 'Police - Local Law Enforcement' },
  { name: 'Pollution', dept: 'Pollution Control Board' },
  { name: 'Public Transport', dept: 'State Transport' },
  { name: 'Parks & Trees', dept: 'Municipal - Horticulture' },
];

export default function Home() {
  return (
    <div className="bg-white">
      {/* --- HERO BANNER --- */}
      <section className="bg-linear-to-br from-primary-dark via-primary to-primary-light relative overflow-hidden">
        {/* Subtle pattern overlay */}
        <div className="absolute inset-0 opacity-5" style={{backgroundImage: 'radial-gradient(circle at 1px 1px, white 1px, transparent 0)', backgroundSize: '32px 32px'}} />
        
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 sm:py-24 lg:py-28">
          <div className="flex flex-col lg:flex-row items-center gap-12">
            {/* Left Text */}
            <div className="flex-1 text-center lg:text-left">
              <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-white/10 border border-white/20 text-saffron text-sm font-medium mb-6">
                <Shield className="w-4 h-4" />
                Government of India Initiative
              </div>
              
              <h1 className="govt-heading text-3xl sm:text-4xl lg:text-5xl text-white mb-6">
                जन-सुनवाई
                <span className="block text-xl sm:text-2xl lg:text-3xl text-blue-200 font-normal mt-2">
                  Public Grievance Redressal System
                </span>
              </h1>
              
              <p className="text-blue-100 text-base sm:text-lg max-w-xl leading-relaxed mb-8">
                Report civic issues with photographic evidence. Our AI-powered system automatically identifies the problem, 
                determines the responsible department, and drafts an official complaint — all in seconds.
              </p>

              <div className="flex flex-col sm:flex-row gap-4 justify-center lg:justify-start">
                <Link
                  to="/analyze"
                  className="inline-flex items-center justify-center gap-2 bg-saffron hover:bg-saffron-light text-white px-6 py-3 rounded font-semibold text-base transition shadow-lg hover:shadow-xl"
                >
                  File a Complaint
                  <ArrowRight className="w-5 h-5" />
                </Link>
                <a 
                  href="#how-it-works" 
                  className="inline-flex items-center justify-center gap-2 bg-white/10 hover:bg-white/20 border border-white/25 text-white px-6 py-3 rounded font-medium text-base transition"
                >
                  How It Works
                </a>
              </div>
            </div>

            {/* Right - Stats / Trust block */}
            <div className="shrink-0 w-full lg:w-auto">
              <div className="grid grid-cols-2 gap-4 max-w-sm mx-auto lg:mx-0">
                <div className="bg-white/10 backdrop-blur border border-white/15 rounded-lg p-5 text-center">
                  <Building2 className="w-7 h-7 text-saffron mx-auto mb-2" />
                  <div className="text-2xl font-bold text-white">11</div>
                  <div className="text-xs text-blue-200 mt-1">Departments Covered</div>
                </div>
                <div className="bg-white/10 backdrop-blur border border-white/15 rounded-lg p-5 text-center">
                  <Clock className="w-7 h-7 text-saffron mx-auto mb-2" />
                  <div className="text-2xl font-bold text-white">&lt;30s</div>
                  <div className="text-xs text-blue-200 mt-1">Processing Time</div>
                </div>
                <div className="bg-white/10 backdrop-blur border border-white/15 rounded-lg p-5 text-center">
                  <Shield className="w-7 h-7 text-saffron mx-auto mb-2" />
                  <div className="text-2xl font-bold text-white">100%</div>
                  <div className="text-xs text-blue-200 mt-1">Local Processing</div>
                </div>
                <div className="bg-white/10 backdrop-blur border border-white/15 rounded-lg p-5 text-center">
                  <CheckCircle2 className="w-7 h-7 text-saffron mx-auto mb-2" />
                  <div className="text-2xl font-bold text-white">AI</div>
                  <div className="text-xs text-blue-200 mt-1">Auto Classification</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* --- HOW IT WORKS --- */}
      <section id="how-it-works" className="py-16 sm:py-24 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-14">
            <h2 className="text-sm font-bold text-saffron uppercase tracking-widest mb-2">Process</h2>
            <p className="govt-heading text-2xl sm:text-3xl text-gray-900">
              How Your Complaint is Processed
            </p>
            <p className="mt-4 text-gray-600 max-w-2xl mx-auto">
              Three simple steps from photo to official record. No paperwork, no queues.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 lg:gap-12">
            {/* Step 1 */}
            <div className="relative text-center group">
              <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-primary text-white text-xl font-bold mb-5 group-hover:scale-110 transition-transform">
                1
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Upload Evidence</h3>
              <p className="text-gray-600 text-sm leading-relaxed">
                Take a photo of the civic issue and upload it. GPS location is automatically extracted from the image metadata.
              </p>
              <div className="hidden md:block absolute top-7 left-[60%] w-[80%] border-t-2 border-dashed border-gray-200" />
            </div>

            {/* Step 2 */}
            <div className="relative text-center group">
              <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-primary text-white text-xl font-bold mb-5 group-hover:scale-110 transition-transform">
                2
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">AI Analysis</h3>
              <p className="text-gray-600 text-sm leading-relaxed">
                Computer vision identifies the issue type (pothole, garbage, broken light, etc.) and routes it to the correct government department.
              </p>
              <div className="hidden md:block absolute top-7 left-[60%] w-[80%] border-t-2 border-dashed border-gray-200" />
            </div>

            {/* Step 3 */}
            <div className="text-center group">
              <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-primary text-white text-xl font-bold mb-5 group-hover:scale-110 transition-transform">
                3
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Official Complaint</h3>
              <p className="text-gray-600 text-sm leading-relaxed">
                An AI-generated formal complaint letter is drafted and sent to the responsible department for resolution.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* --- CATEGORIES COVERED --- */}
      <section className="py-16 sm:py-20 bg-gray-50 border-t border-gray-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-sm font-bold text-saffron uppercase tracking-widest mb-2">Departments</h2>
            <p className="govt-heading text-2xl sm:text-3xl text-gray-900">
              Issues We Handle
            </p>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
            {CATEGORIES.map(({ name, dept }) => (
              <div
                key={dept}
                className="bg-white border border-gray-150 rounded-lg px-4 py-3.5 text-center hover:border-primary/30 hover:shadow-sm transition group"
              >
                <p className="text-sm font-medium text-gray-800 group-hover:text-primary transition">{name}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* --- CTA / FOOTER BANNER --- */}
      <section className="bg-primary-dark py-12 sm:py-16">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <h2 className="govt-heading text-2xl sm:text-3xl text-white mb-4">
            Your City, Your Voice
          </h2>
          <p className="text-blue-200 mb-8 max-w-xl mx-auto">
            Every complaint filed helps improve civic infrastructure. Report issues today and track their resolution.
          </p>
          <Link
            to="/register"
            className="inline-flex items-center gap-2 bg-saffron hover:bg-saffron-light text-white px-8 py-3 rounded font-semibold text-base transition shadow-lg"
          >
            Register Now
            <ArrowRight className="w-5 h-5" />
          </Link>
        </div>
      </section>

      {/* --- FOOTER --- */}
      <footer className="bg-gray-900 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2 text-gray-400 text-sm">
              <span className="text-saffron text-lg">&#9784;</span>
              <span>जन-सुनवाई — Public Grievance Redressal System</span>
            </div>
            <div className="text-gray-500 text-xs">
              Built with AI for transparent governance. All data processed locally.
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
