import React from 'react';
import {
  X,
  Shield,
  Clock,
  Radio,
  FileCheck2,
  Users,
  AlertTriangle,
  Lightbulb,
  CheckCircle2,
  Network,
  Cpu,
  ArrowRight,
} from 'lucide-react';

interface AboutModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const AboutModal: React.FC<AboutModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 9999,
        backgroundColor: 'rgba(5, 8, 15, 0.85)',
        backdropFilter: 'blur(6px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '20px',
      }}
      onClick={onClose}
    >
      <div
        style={{
          backgroundColor: '#0c1222',
          border: '1px solid rgba(56, 189, 248, 0.3)',
          borderRadius: '16px',
          width: '100%',
          maxWidth: '820px',
          maxHeight: '90vh',
          display: 'flex',
          flexDirection: 'column',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.7), 0 0 30px rgba(2, 132, 199, 0.15)',
          overflow: 'hidden',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header Modal */}
        <div
          style={{
            padding: '20px 24px',
            borderBottom: '1px solid rgba(51, 65, 85, 0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            background: 'linear-gradient(90deg, rgba(12, 18, 34, 1) 0%, rgba(15, 23, 42, 1) 100%)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div
              style={{
                background: 'linear-gradient(135deg, #0284c7, #06b6d4)',
                borderRadius: '10px',
                padding: '8px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Shield size={22} color="#ffffff" />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <h2 style={{ fontSize: '1.15rem', fontWeight: 700, color: '#f8fafc', margin: 0 }}>
                  Tentang CaRI-Siber ID & Panduan Pengguna
                </h2>
                <span
                  style={{
                    backgroundColor: 'rgba(234, 179, 8, 0.15)',
                    color: '#facc15',
                    border: '1px solid rgba(234, 179, 8, 0.4)',
                    fontSize: '0.65rem',
                    fontWeight: 700,
                    padding: '2px 8px',
                    borderRadius: '20px',
                    letterSpacing: '0.05em',
                  }}
                >
                  PROTOTIPE / PoC
                </span>
              </div>
              <div style={{ fontSize: '0.78rem', color: '#94a3b8', marginTop: '2px' }}>
                Sistem Intelijen Kognitif, Deteksi Operasi Informasi (CIB), & Forensik Bukti Digital
              </div>
            </div>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#94a3b8',
              cursor: 'pointer',
              padding: '6px',
              borderRadius: '8px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
            title="Tutup (Esc)"
          >
            <X size={20} />
          </button>
        </div>

        {/* Body Content */}
        <div
          style={{
            padding: '24px',
            overflowY: 'auto',
            display: 'flex',
            flexDirection: 'column',
            gap: '20px',
            color: '#cbd5e1',
            fontSize: '0.875rem',
            lineHeight: 1.6,
          }}
        >
          {/* NOTICE: Status Prototipe & Visi 24/7 */}
          <div
            style={{
              backgroundColor: 'rgba(234, 179, 8, 0.08)',
              border: '1px solid rgba(234, 179, 8, 0.3)',
              borderRadius: '12px',
              padding: '16px',
              display: 'flex',
              gap: '14px',
            }}
          >
            <AlertTriangle size={24} color="#facc15" style={{ flexShrink: 0, marginTop: '2px' }} />
            <div>
              <div style={{ fontWeight: 700, color: '#fef08a', fontSize: '0.92rem', marginBottom: '4px' }}>
                Penegasan Status: Prototipe Cepat (Proof-of-Concept)
              </div>
              <p style={{ margin: 0, color: '#e2e8f0', fontSize: '0.84rem' }}>
                Aplikasi desktop ini adalah <strong>prototipe fungsional (PoC)</strong> yang dikembangkan dalam kurun waktu singkat untuk membuktikan keandalan pipeline AI, pemodelan topik lokal (IndoBERT), dan deteksi buzzer. 
                Saat ini aplikasi bekerja berbasis <em>batch snapshot</em> (per video YouTube atau impor berkas bukti). 
                <strong> Visi ke depan:</strong> Sistem ini dirancang untuk di-scale menjadi <strong>Sistem Otomatis 24/7</strong> berbasis server yang terus memantau arus percakapan media sosial (X/Twitter, TikTok, Instagram, YouTube, Telegram) tanpa jeda waktu dan mengirimkan peringatan dini (*early warning*) secara instan.
              </p>
            </div>
          </div>

          {/* Bagian 1: Untuk Orang Awam: Masalah Apa yang Dipecahkan? */}
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
              <Lightbulb size={18} color="#38bdf8" />
              <h3 style={{ fontSize: '0.98rem', fontWeight: 700, color: '#f1f5f9', margin: 0 }}>
                Untuk Orang Awam: Mengapa Aplikasi Ini Dibuat?
              </h3>
            </div>
            <p style={{ margin: '0 0 10px 0', color: '#94a3b8' }}>
              Pernahkah Anda melihat kolom komentar di media sosial dipenuhi oleh ribuan komentar yang isinya seragam, saling hujat, menyebarkan hoaks, atau memprovokasi isu suku dan agama? Sering kali itu <strong>bukan suara asli masyarakat</strong>, melainkan hasil rekayasa dari <strong>pasukan bot dan buzzer bayaran</strong>.
            </p>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(230px, 1fr))',
                gap: '12px',
                marginTop: '8px',
              }}
            >
              <div
                style={{
                  backgroundColor: '#131c31',
                  padding: '12px 14px',
                  borderRadius: '10px',
                  border: '1px solid rgba(51, 65, 85, 0.4)',
                }}
              >
                <div style={{ fontWeight: 700, color: '#38bdf8', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Users size={15} /> 1. Membedakan Warga vs Bot
                </div>
                <div style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
                  Mendeteksi komentar <em>copypasta</em> (teks seragam disebar serentak) untuk membongkar jaringan akun palsu/buzzer (*Coordinated Inauthentic Behavior*).
                </div>
              </div>

              <div
                style={{
                  backgroundColor: '#131c31',
                  padding: '12px 14px',
                  borderRadius: '10px',
                  border: '1px solid rgba(51, 65, 85, 0.4)',
                }}
              >
                <div style={{ fontWeight: 700, color: '#f87171', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <AlertTriangle size={15} /> 2. Pemetaan Provokator
                </div>
                <div style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
                  Mengklasifikasi bahaya komentar ke dalam 6 domain ancaman (Disinformasi, Propaganda, Hasutan Kekerasan, SARA, Serangan Siber, atau Aspirasi Warga).
                </div>
              </div>

              <div
                style={{
                  backgroundColor: '#131c31',
                  padding: '12px 14px',
                  borderRadius: '10px',
                  border: '1px solid rgba(51, 65, 85, 0.4)',
                }}
              >
                <div style={{ fontWeight: 700, color: '#34d399', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <FileCheck2 size={15} /> 3. Segel Bukti Forensik
                </div>
                <div style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
                  Setiap data yang diunduh langsung disegel secara kriptografis menggunakan algoritma <strong>SHA-256</strong> agar barang bukti sah dan tidak bisa dimanipulasi (*Chain of Custody*).
                </div>
              </div>
            </div>
          </div>

          {/* Bagian 2: Cara Kerja 5 Langkah Sederhana */}
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
              <Cpu size={18} color="#a78bfa" />
              <h3 style={{ fontSize: '0.98rem', fontWeight: 700, color: '#f1f5f9', margin: 0 }}>
                Cara Kerja Pipeline (Dari Data Mentah Menjadi Keputusan)
              </h3>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {[
                {
                  step: 'Langkah 1: Akuisisi Data',
                  desc: 'Mengambil komentar dari YouTube atau mengimpor berkas CSV/Excel dari platform medsos lain secara offline.',
                },
                {
                  step: 'Langkah 2: Pembersihan Bahasa Gaul & Slang',
                  desc: 'Menggunakan kamus bahasa Indonesia untuk menormalkan singkatan dan slang (misal: "yg" → "yang", "bgt" → "banget").',
                },
                {
                  step: 'Langkah 3: Pemodelan Topik Cerdas (IndoBERT)',
                  desc: 'Mengelompokkan ribuan komentar ke dalam klaster topik utama secara otomatis tanpa membaca satu per satu.',
                },
                {
                  step: 'Langkah 4: Verifikasi Bebas Halusinasi (4 Agentic Gates)',
                  desc: 'Menyaring hasil dengan 4 lapis filter verifikasi AI agar angka dan kesimpulan faktual serta dapat dipertanggungjawabkan.',
                },
                {
                  step: 'Langkah 5: Peta Situasi (SITREP) & Laporan Eksekutif',
                  desc: 'Menampilkan skor ancaman, polarisasi kubu, akun provokator, serta mengekspor laporan KIRKA berformat Excel.',
                },
              ].map((item, idx) => (
                <div
                  key={idx}
                  style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '10px',
                    padding: '8px 12px',
                    backgroundColor: 'rgba(15, 23, 42, 0.6)',
                    borderRadius: '8px',
                    borderLeft: '3px solid #38bdf8',
                  }}
                >
                  <CheckCircle2 size={16} color="#38bdf8" style={{ flexShrink: 0, marginTop: '2px' }} />
                  <div>
                    <span style={{ fontWeight: 700, color: '#f1f5f9', fontSize: '0.84rem' }}>{item.step}: </span>
                    <span style={{ color: '#94a3b8', fontSize: '0.82rem' }}>{item.desc}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Bagian 3: Rencana Evolusi Menuju Monitoring 24/7 */}
          <div
            style={{
              backgroundColor: 'rgba(2, 132, 199, 0.08)',
              border: '1px solid rgba(2, 132, 199, 0.25)',
              borderRadius: '12px',
              padding: '16px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
              <Radio size={18} color="#38bdf8" />
              <h4 style={{ fontSize: '0.92rem', fontWeight: 700, color: '#38bdf8', margin: 0 }}>
                Arsitektur Masa Depan: Pemantauan Siber 24/7 Non-Stop
              </h4>
            </div>
            <p style={{ margin: '0 0 10px 0', fontSize: '0.82rem', color: '#94a3b8' }}>
              Jika diimplementasikan pada skala penuh, sistem ini tidak lagi menunggu pengguna menekan tombol analisis manual, melainkan:
            </p>
            <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '0.82rem', color: '#cbd5e1', display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <li><strong>Continuous Crawling Daemon:</strong> Pekerja latar belakang (*background workers*) memantau trending topic YouTube, X, TikTok, dan Telegram 24 jam nonstop.</li>
              <li><strong>Real-time Alerting:</strong> Peringatan instan ke Puskodal atau bot Telegram saat terdeteksi lonjakan operasi buzzer atau ancaman siber baru.</li>
              <li><strong>Centralized Database & Graph Correlation:</strong> Melacak jaringan akun buzzer lintas platform dalam jangka waktu berbulan-bulan menggunakan basis data grafis.</li>
            </ul>
          </div>
        </div>

        {/* Footer Modal */}
        <div
          style={{
            padding: '14px 24px',
            borderTop: '1px solid rgba(51, 65, 85, 0.5)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            backgroundColor: '#090d16',
          }}
        >
          <div style={{ fontSize: '0.75rem', color: '#64748b' }}>
            CaRI-Siber ID • Versi Prototipe Cepat (UNSIA Capstone Project)
          </div>
          <button
            onClick={onClose}
            style={{
              padding: '8px 18px',
              backgroundColor: '#0284c7',
              color: '#ffffff',
              border: 'none',
              borderRadius: '8px',
              fontSize: '0.82rem',
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'background 0.2s',
            }}
          >
            Paham, Lanjutkan
          </button>
        </div>
      </div>
    </div>
  );
};
