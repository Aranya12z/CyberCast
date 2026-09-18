import React from 'react';
import {
  Shield,
  ArrowLeft,
  Lock,
  Database,
  Eye,
  FileText,
  Mail,
  UserCheck,
  Share2,
  Clock,
  AlertTriangle
} from 'lucide-react';
import { useApp } from '../state/AppContext';

const Section = ({ icon: Icon, title, children }) => (
  <section className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3">
    <h2 className="text-sm font-semibold text-white flex items-center gap-2">
      <Icon size={15} className="text-indigo-400 flex-shrink-0" />
      <span>{title}</span>
    </h2>
    <div className="space-y-2 text-slate-400 leading-relaxed text-xs">
      {children}
    </div>
  </section>
);

export const PrivacyPolicy = () => {
  const { setActiveTab } = useApp();

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-12">

      {/* Back Button */}
      <div>
        <button
          onClick={() => setActiveTab('overview')}
          className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 text-xs font-medium border border-slate-800 transition"
        >
          <ArrowLeft size={14} />
          <span>Return to Dashboard</span>
        </button>
      </div>

      {/* Header */}
      <div className="p-6 rounded-xl bg-slate-900/90 border border-slate-800 space-y-2">
        <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-md bg-slate-800 text-slate-300 text-xs font-mono border border-slate-700">
          <Shield size={13} className="text-indigo-400" />
          <span>PROTOTYPE DOCUMENTATION</span>
        </div>
        <h1 className="text-2xl font-bold text-white tracking-tight">
          Privacy Policy
        </h1>
        <p className="text-xs text-slate-400 leading-relaxed">
          Effective Date: September 2026. This document explains data handling practices for the CyberCast
          predictive analytics research prototype developed for the Smart India Hackathon (SIH 2026).
        </p>
      </div>

      {/* Prototype Notice */}
      <div className="p-4 rounded-xl bg-slate-900 border border-amber-900/40 text-xs text-slate-300 space-y-1.5">
        <div className="font-semibold text-amber-300 uppercase font-mono text-[11px] flex items-center gap-1.5">
          <AlertTriangle size={13} className="text-amber-400" />
          <span>Prototype and Demonstration Notice</span>
        </div>
        <p className="text-slate-400 leading-relaxed">
          CyberCast is an academic and hackathon prototype designed to demonstrate predictive intelligence
          concepts. It is not deployed as an official government, law enforcement, or financial production system.
          All data processed in the current implementation is synthetic, anonymized, and simulated. No real
          personal data, banking records, or law enforcement case files are used or stored.
        </p>
      </div>

      {/* Sections */}
      <div className="space-y-4 text-xs">

        <Section icon={FileText} title="1. Introduction">
          <p>
            This Privacy Policy describes how data is handled within the CyberCast predictive analytics
            prototype. CyberCast is a demonstration system developed as part of the Smart India Hackathon
            (SIH 2026) to evaluate the technical feasibility of predicting likely cash withdrawal locations
            following a cybercrime event.
          </p>
          <p>
            By accessing and using this prototype, you acknowledge that you have read and understood this
            Privacy Policy and the limitations it describes.
          </p>
        </Section>

        <Section icon={Database} title="2. Information and Data Used">
          <p>
            The CyberCast prototype processes the following categories of data for demonstration purposes:
          </p>
          <ul className="list-disc list-inside space-y-1 text-slate-300 pl-2">
            <li>Synthetic cybercrime incident records: identifiers, incident categories, timestamps, and approximate geographic coordinates.</li>
            <li>Simulated financial transaction records: reference codes, monetary amounts, and timestamps. No real account numbers or customer identities are used.</li>
            <li>ATM registry data: machine identifiers, bank labels, district-level location coordinates, and simulated risk and confidence scores.</li>
            <li>Geospatial coordinates (latitude and longitude) used to compute spatial proximity between incident origins and candidate ATM locations.</li>
            <li>Dashboard session context: the currently selected role (investigator, bank analyst, or administrator) stored locally in the browser session for demonstration purposes.</li>
          </ul>
          <p>
            No real personal identities, real financial account details, real law enforcement case files, or
            any sensitive personal data are stored or processed in this demonstration environment.
          </p>
        </Section>

        <Section icon={Eye} title="3. How Data Is Used">
          <p>
            Information processed within this prototype is used solely for the following technical objectives:
          </p>
          <ul className="list-disc list-inside space-y-1 text-slate-300 pl-2">
            <li>Generating ranked candidate withdrawal locations based on spatial, temporal, and transactional feature signals.</li>
            <li>Assigning risk likelihood scores and model confidence estimates to candidate ATM locations.</li>
            <li>Rendering candidate locations on an interactive GIS dashboard for investigator review.</li>
            <li>Generating actionable alerts when candidate predictions meet agreed risk and confidence thresholds (ADR-006).</li>
            <li>Demonstrating investigation workflows for law enforcement and financial institution collaboration.</li>
          </ul>
          <p>
            Data is not used for advertising, commercial profiling, or any purpose beyond this technical
            demonstration.
          </p>
        </Section>

        <Section icon={Lock} title="4. Data Security">
          <p>
            Security controls implemented in this prototype are proportionate to its academic demonstration scope:
          </p>
          <ul className="list-disc list-inside space-y-1 text-slate-300 pl-2">
            <li>Role-based access control is demonstrated through a simulated role switcher (investigator, bank analyst, administrator).</li>
            <li>No real credentials, API keys, or secrets are stored in source-controlled files. Environment variables are used for configuration.</li>
            <li>The frontend communicates with the backend over local network connections in the demonstration environment.</li>
            <li>No real cryptographic or compliance certifications (such as ISO 27001, SOC 2, or PCI-DSS) are claimed for this prototype.</li>
          </ul>
        </Section>

        <Section icon={Share2} title="5. Data Sharing">
          <p>
            No data processed within this prototype is shared with external parties for commercial, analytical,
            or operational purposes. The only third-party service involved is the loading of publicly available
            map tile imagery from OpenStreetMap contributors and CartoDB for the GIS visualization layer.
            Standard map tile requests do not transmit complaint data, prediction outputs, or user session
            details to mapping providers.
          </p>
        </Section>

        <Section icon={Clock} title="6. Data Retention">
          <p>
            Demonstration datasets, simulated prediction runs, and alert acknowledgement records are stored in
            a local database instance for the duration of each evaluation session. These records can be reset
            or purged by restarting or reinitializing the local database. No persistent commercial data
            warehousing, cloud-based backup, or long-term log archiving is implemented in this prototype.
          </p>
          <p>
            Acknowledged alert states maintained in the browser's local storage are cleared automatically when
            the browser session is reset.
          </p>
        </Section>

        <Section icon={UserCheck} title="7. User and Investigator Responsibilities">
          <p>
            Users accessing this prototype agree to the following:
          </p>
          <ul className="list-disc list-inside space-y-1 text-slate-300 pl-2">
            <li>You will not introduce real personal financial information, real law enforcement case data, or sensitive personal records into the prototype environment.</li>
            <li>You will not share screenshots or outputs of this prototype in a manner that misrepresents prediction results as verified or operational intelligence.</li>
            <li>You acknowledge that all data presented in the dashboard is synthetic and for demonstration purposes only.</li>
            <li>You will maintain awareness that prediction outputs are probabilistic rankings, not guaranteed facts.</li>
          </ul>
        </Section>

        <Section icon={AlertTriangle} title="8. Prototype and Demo Data Notice">
          <p>
            All incident records, ATM data, prediction results, risk scores, confidence values, and alert
            outputs displayed in this system are generated from synthetic, simulated, or anonymized datasets
            created specifically for the Smart India Hackathon evaluation environment.
          </p>
          <p>
            These outputs do not represent real cybercrime investigations, real financial institutions, real
            ATM locations, or real law enforcement operations. Any resemblance to actual events, organizations,
            or individuals is coincidental.
          </p>
          <p>
            CyberCast outputs must not be used as the sole basis for any law enforcement action, financial
            decision, or legal proceeding.
          </p>
        </Section>

        <Section icon={Mail} title="9. Contact">
          <p>
            For academic inquiries, questions about this prototype, or clarification regarding data handling
            practices, please contact the CyberCast project team at:
          </p>
          <p className="font-mono text-indigo-300 mt-1">
            [Project contact email]
          </p>
          <p className="mt-2">
            This Privacy Policy may be revised as the prototype evolves during the evaluation period.
          </p>
        </Section>

      </div>
    </div>
  );
};
