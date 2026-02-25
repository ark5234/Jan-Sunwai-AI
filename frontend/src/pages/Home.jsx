import React from 'react';
import { Link } from 'react-router-dom';
import { Upload, MapPin, FileCheck } from 'lucide-react';

export default function Home() {
  return (
    <div className="bg-white">
      {/* Hero Section */}
      <div className="relative isolate px-6 pt-14 lg:px-8">
        <div className="mx-auto max-w-2xl py-12 sm:py-28 lg:py-26">
          <div className="text-center">
            <h1 className="text-4xl font-bold tracking-tight text-slate-900 sm:text-6xl">
              Fix Your City with <span className="text-primary">AI Speed</span>
            </h1>
            <p className="mt-6 text-lg leading-8 text-slate-600">
              Transforming civic grievances into formal action. Upload a photo, let AI analyze the issue, and generate an official complaint letter in seconds.
            </p>
            <div className="mt-10 flex items-center justify-center gap-x-6">
              <Link
                to="/analyze"
                className="rounded-md bg-primary px-3.5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-blue-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
              >
                Start New Complaint
              </Link>
              <a href="#how-it-works" className="text-sm font-semibold leading-6 text-slate-900">
                Learn more <span aria-hidden="true">→</span>
              </a>
            </div>
          </div>
        </div>
      </div>

      {/* Feature Section */}
      <div id="how-it-works" className="bg-slate-50 py-24 sm:py-32">
        <div className="mx-auto max-w-7xl px-6 lg:px-8">
          <div className="mx-auto max-w-2xl lg:text-center">
            <h2 className="text-base font-semibold leading-7 text-primary">Deploy AI</h2>
            <p className="mt-2 text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
              From Photo to Official Record
            </p>
            <p className="mt-6 text-lg leading-8 text-slate-600">
              We use Computer Vision to identify potholes, garbage, and unmaintained parks, then use LLMs to write the perfect letter.
            </p>
          </div>
          <div className="mx-auto mt-16 max-w-2xl sm:mt-20 lg:mt-24 lg:max-w-4xl">
            <dl className="grid max-w-xl grid-cols-1 gap-x-8 gap-y-10 lg:max-w-none lg:grid-cols-3 lg:gap-y-16">
              <div className="relative pl-16">
                <dt className="text-base font-semibold leading-7 text-slate-900">
                  <div className="absolute left-0 top-0 flex h-10 w-10 items-center justify-center rounded-lg bg-primary">
                    <Upload className="h-6 w-6 text-white" aria-hidden="true" />
                  </div>
                  Snap & Upload
                </dt>
                <dd className="mt-2 text-base leading-7 text-slate-600">Take a photo of the issue. Our system accepts standard formats and filters out invalid images.</dd>
              </div>
              <div className="relative pl-16">
                <dt className="text-base font-semibold leading-7 text-slate-900">
                  <div className="absolute left-0 top-0 flex h-10 w-10 items-center justify-center rounded-lg bg-primary">
                    <MapPin className="h-6 w-6 text-white" aria-hidden="true" />
                  </div>
                  Geotag & Classify
                </dt>
                <dd className="mt-2 text-base leading-7 text-slate-600">We extract GPS data and use OpenAI CLIP to detect if it's a sanitation, road, or electrical issue.</dd>
              </div>
              <div className="relative pl-16">
                <dt className="text-base font-semibold leading-7 text-slate-900">
                  <div className="absolute left-0 top-0 flex h-10 w-10 items-center justify-center rounded-lg bg-primary">
                    <FileCheck className="h-6 w-6 text-white" aria-hidden="true" />
                  </div>
                  Draft & Send
                </dt>
                <dd className="mt-2 text-base leading-7 text-slate-600">Ollama AI writes a compliant formal letter addressed to the exact municipal department.</dd>
              </div>
            </dl>
          </div>
        </div>
      </div>
    </div>
  );
}
