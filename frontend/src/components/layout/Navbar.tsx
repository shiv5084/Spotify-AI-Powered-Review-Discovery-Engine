'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import styles from '../../styles/navbar.module.css';
import ConsoleModal from './ConsoleModal';

interface NavbarProps {
  weekEnding?: string;
}

export default function Navbar({ weekEnding = 'N/A' }: NavbarProps) {
  const [isConsoleOpen, setIsConsoleOpen] = useState(false);
  const router = useRouter();

  const handleRunPipeline = () => {
    setIsConsoleOpen(true);
  };

  const handlePipelineComplete = () => {
    // Refresh the router to refetch Server Component data (re-reads dashboard_data.json)
    router.refresh();
  };

  return (
    <>
      <nav className={styles.navbar}>
        <div className={styles.logoContainer}>
          <div className={styles.logoIcon}>
            <svg viewBox="0 0 24 24">
              <path d="M12 2C6.477 2 2 6.477 2 12s4.477 10 10 10 10-4.477 10-10S17.523 2 12 2zm4.586 14.424c-.18.295-.565.387-.86.207-2.377-1.454-5.37-1.783-8.894-.98-.336.075-.67-.135-.747-.472-.077-.336.136-.67.472-.747 3.854-.88 7.15-.506 9.822 1.13.295.18.387.563.207.862zm1.225-2.72c-.226.367-.707.487-1.074.26-2.72-1.672-6.87-2.157-10.078-1.182-.413.125-.847-.107-.972-.52-.125-.413.108-.847.52-.973 3.67-1.114 8.24-.57 11.344 1.34.367.227.487.708.26 1.075zm.107-2.846C14.512 8.807 9.043 8.625 5.887 9.585c-.482.146-.988-.128-1.134-.61-.147-.482.128-.988.61-1.134 3.642-1.105 9.77-.894 13.717 1.45.434.257.577.813.32 1.247-.257.433-.814.576-1.247.32z"/>
            </svg>
          </div>
          <div>
            <h1 className={styles.title}>Spotify PRDE</h1>
            <span className={styles.subtitle}>Review Discovery Engine</span>
          </div>
        </div>

        <div className={styles.metaInfo}>
          <div className={styles.weekLabel}>
            Week Ending: <span className={styles.weekValue}>{weekEnding}</span>
          </div>
          <button 
            onClick={handleRunPipeline} 
            className={styles.runButton}
            disabled={isConsoleOpen}
          >
            {isConsoleOpen ? (
              <>
                <span style={{
                  display: 'inline-block',
                  width: '12px',
                  height: '12px',
                  border: '2px solid #000',
                  borderTop: '2px solid transparent',
                  borderRadius: '50%',
                  animation: 'spin 1s linear infinite'
                }} />
                Running...
              </>
            ) : (
              <>
                <svg style={{ width: '14px', height: '14px', fill: 'currentColor' }} viewBox="0 0 24 24">
                  <path d="M8 5v14l11-7z"/>
                </svg>
                Run Pipeline
              </>
            )}
          </button>
        </div>

        <style jsx global>{`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}</style>
      </nav>

      <ConsoleModal 
        isOpen={isConsoleOpen} 
        onClose={() => setIsConsoleOpen(false)} 
        onComplete={handlePipelineComplete}
      />
    </>
  );
}

