'use client'

import Link from 'next/link'
import { motion } from 'framer-motion'
import { Sprout, ArrowRight, Leaf, Activity } from 'lucide-react'

const features = [
  {
    icon: Activity,
    title: 'Multi-Agent Analysis',
    description: 'Our system uses specialized AI agents for vision analysis, diagnosis, evidence gathering, and treatment recommendations'
  },
  {
    icon: Sprout,
    title: 'Image-Based Diagnosis',
    description: 'Upload plant images to receive detailed disease detection with confidence scores and treatment suggestions'
  },
  {
    icon: Leaf,
    title: 'Evidence-Based Results',
    description: 'Every diagnosis includes supporting evidence, observed symptoms, and explainable AI reasoning'
  }
]

export default function Home() {
  return (
    <main>
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-br from-emerald-50 via-white to-green-50">
        <div className="grid-container py-24">
          <div className="col-span-12 text-center">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
            >
              <div className="inline-flex items-center space-x-2 bg-emerald-100 text-emerald-700 px-4 py-2 rounded-full text-sm font-medium mb-6">
                <Leaf className="w-4 h-4" />
                <span>Multi-Agent Agricultural Intelligence</span>
              </div>
              
              <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold tracking-tight mb-6">
                <span className="text-emerald-600">AgriSense</span> AI
              </h1>
              
              <p className="text-2xl md:text-3xl text-gray-600 mb-4">
                Agricultural Disease Diagnosis Platform
              </p>
              
              <p className="max-w-2xl mx-auto text-lg text-gray-600 mb-8">
                Upload plant images for AI-powered disease detection using our multi-agent system. 
                Get detailed analysis with evidence-based reasoning and treatment recommendations.
              </p>
              
              <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                <Link href="/diagnosis" className="btn-primary text-lg px-8 py-3 flex items-center space-x-2">
                  <span>Start Diagnosis</span>
                  <ArrowRight className="w-5 h-5" />
                </Link>
                <Link href="/dashboard" className="btn-secondary text-lg px-8 py-3">
                  View Dashboard
                </Link>
              </div>
            </motion.div>
          </div>
        </div>
        
        {/* Decorative Elements */}
        <div className="absolute top-20 left-10 w-20 h-20 bg-emerald-200 rounded-full opacity-20 blur-xl" />
        <div className="absolute bottom-20 right-10 w-32 h-32 bg-green-200 rounded-full opacity-20 blur-xl" />
        <div className="absolute top-40 right-1/4 w-16 h-16 bg-emerald-300 rounded-full opacity-10 blur-lg" />
      </section>

      {/* Features Section */}
      <section className="py-24 bg-gray-50">
        <div className="grid-container">
          <div className="col-span-12 text-center mb-16">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
            >
              <h2 className="text-4xl font-bold mb-4">How It Works</h2>
              <p className="text-lg text-gray-600 max-w-2xl mx-auto">
                Our multi-agent system provides comprehensive plant disease analysis
              </p>
            </motion.div>
          </div>
          
          <div className="col-span-12">
            <div className="grid md:grid-cols-3 gap-8">
              {features.map((feature, index) => (
                <motion.div
                  key={feature.title}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, delay: index * 0.1 }}
                >
                  <div className="card h-full hover:shadow-lg transition-shadow">
                    <div className="p-4 rounded-xl bg-emerald-100 w-fit mb-4">
                      <feature.icon className="w-8 h-8 text-emerald-600" />
                    </div>
                    <h3 className="text-xl font-semibold mb-3">{feature.title}</h3>
                    <p className="text-gray-600">{feature.description}</p>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-12">
        <div className="grid-container">
          <div className="col-span-12 text-center">
            <div className="flex items-center justify-center space-x-2 mb-4">
              <Sprout className="w-6 h-6 text-emerald-400" />
              <span className="text-xl font-bold">AgriSense AI</span>
            </div>
            <p className="text-gray-400 mb-4">
              Multi-Agent Agricultural Disease Diagnosis System
            </p>
            <p className="text-gray-500 text-sm">
              © 2026 AgriSense AI. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </main>
  )
}
