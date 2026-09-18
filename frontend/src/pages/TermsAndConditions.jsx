import React from 'react';
import {
  FileText,
  ArrowLeft,
  AlertTriangle,
  ShieldCheck,
  HelpCircle,
  CheckSquare,
  Scale,
  Mail,
  UserCheck,
  Target,
  XCircle,
  RefreshCw
} from 'lucide-react';
import { useApp } from '../state/AppContext';

const Section = ({ icon: Icon, title, children, accent }) => (
  <section className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3">
    <h2 className="text-sm font-semibold text-white flex items-center gap-2">
      <Icon size={15} className={accent ? 'text-amber-400 flex-shrink-0' : 'text-indigo-400 flex-shrink-0'} />
      <span>{title}</span>
    </h2>
    <div className="space-y-2 text-slate-400 leading-relaxed text-xs">
      {children}
    </div>
  </section>
);

export const TermsAndConditions = () => {
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
          <FileText size={13} className="text-indigo-400" />
          <span>PROTOTYPE DOCUMENTATION</span>
        </div>
        <h1 className="text-2xl font-bold text-white tracking-tight">
          Terms and Conditions
        </h1>
        <p className="text-xs text-slate-400 leading-relaxed">
          Effective Date: September 2026. These terms govern the use and demonstration of the CyberCast
          predictive analytics prototype application developed for the Smart India Hackathon (SIH 2026).
        </p>
      </div>

      {/* Critical Prediction Disclaimer Banner */}
      <div className="p-4 rounded-xl bg-slate-900 border border-amber-900/50 text-xs text-slate-300 space-y-1.5">
        <div className="font-semibold text-amber-300 uppercase font-mono text-[11px] flex items-center gap-1.5">
          <AlertTriangle size={13} className="text-amber-400" />
          <span>Prediction Limitations and Non-Guarantee Disclaimer</span>
        </div>
        <p className="text-slate-400 leading-relaxed">
          CyberCast produces probabilistic, ranked candidate locations based on statistical pattern analysis.
          The system does not guarantee that a cash withdrawal will occur at any designated candidate location
          or within any estimated time window. Prediction outputs and risk scores must not be used as the sole
          basis for law enforcement action, legal proceedings, or financial decisions. Human judgment and
          independent verification are required before acting on any system output.
        </p>
      </div>

      {/* Sections */}
      <div className="space-y-4 text-xs">

        <Section icon={FileText} title="1. Introduction">
          <p>
            These Terms and Conditions apply to the CyberCast prototype application. By accessing or using
            CyberCast, you agree to be bound by these terms. If you do not agree, you should not use this
            prototype.
          </p>
          <p>
            CyberCast is provided solely for academic review, technical evaluation, and demonstration purposes
            as part of the Smart India Hackathon (SIH 2026) competition. It is not an operational law
            enforcement tool, a licensed financial intelligence product, or a certified government system.
          </p>
        </Section>

        <Section icon={Target} title="2. Purpose of CyberCast">
          <p>
            CyberCast is designed to explore the technical feasibility of using machine learning and
            geospatial analysis to predict likely cash withdrawal locations following cybercrime events.
            Specifically, it aims to:
          </p>
          <ul className="list-disc list-inside space-y-1 text-slate-300 pl-2">
            <li>Ingest simulated cybercrime complaint data and financial transaction signals.</li>
            <li>Compute ranked candidate ATM or cash-out locations using trained statistical models.</li>
            <li>Provide explainable risk scores and confidence estimates to authorized dashboard users.</li>
            <li>Generate actionable alerts to support early intervention workflows in a demonstration context.</li>
          </ul>
          <p>
            The system is a predictive intelligence layer, not a replacement for existing cybercrime
            complaint infrastructure or operational law enforcement systems.
          </p>
        </Section>

        <Section icon={CheckSquare} title="3. Acceptable Use">
          <p>
            Authorized evaluators and demonstration users may interact with CyberCast solely within the
            boundaries of hackathon review and academic assessment. The following activities are prohibited:
          </p>
          <ul className="list-disc list-inside space-y-1 text-slate-300 pl-2">
            <li>Introducing real personal financial records, real bank credentials, or real law enforcement case data into the prototype environment.</li>
            <li>Using prototype outputs to initiate actual field operations, arrests, account freezes, or law enforcement actions without independent verification.</li>
            <li>Representing CyberCast prediction outputs as confirmed intelligence or guaranteed facts in any formal report or proceeding.</li>
            <li>Attempting to reverse-engineer, decompile, or disrupt application components beyond normal demonstration use.</li>
            <li>Sharing prediction outputs in a manner that identifies or implicates real individuals or real financial institutions.</li>
          </ul>
        </Section>

        <Section icon={AlertTriangle} title="4. Prototype and Demo Disclaimer" accent>
          <p>
            CyberCast is a student/academic prototype built for the Smart India Hackathon. It is not a
            production system. All incident records, predictions, ATM data, risk scores, confidence values,
            alerts, and other outputs displayed in the dashboard are derived from synthetic, anonymized, and
            simulated datasets created solely for demonstration purposes.
          </p>
          <p>
            This prototype has not been independently audited, certified, or approved by any government
            authority, law enforcement body, or regulatory agency.
          </p>
        </Section>

        <Section icon={XCircle} title="5. Prediction and Risk Score Disclaimer" accent>
          <p>
            Risk scores, confidence values, and ranked candidate locations produced by CyberCast are
            probabilistic estimates generated by machine learning models trained on simulated data. They
            represent statistical likelihoods, not confirmed facts.
          </p>
          <ul className="list-disc list-inside space-y-1 text-slate-300 pl-2">
            <li>A high risk score does not confirm that a crime will occur at a specific location.</li>
            <li>A low confidence value does not confirm that a location is safe or crime-free.</li>
            <li>Predicted time windows are statistical estimates and may not reflect actual event timing.</li>
            <li>Explanation signals indicate statistical feature contributions, not legal evidence of criminal intent.</li>
          </ul>
        </Section>

        <Section icon={HelpCircle} title="6. No Guarantee of Accuracy">
          <p>
            Machine learning models, spatial heuristics, and statistical algorithms utilized in this
            prototype rely on synthetic training datasets. Model outputs may include false positives,
            false negatives, or patterns that do not generalize to real-world conditions.
          </p>
          <p>
            The project team makes no warranty, express or implied, regarding the accuracy, completeness,
            reliability, suitability, or availability of any prediction outputs, alerts, or intelligence
            summaries generated by CyberCast.
          </p>
        </Section>

        <Section icon={UserCheck} title="7. User Responsibilities">
          <p>
            All users of this prototype accept the following responsibilities:
          </p>
          <ul className="list-disc list-inside space-y-1 text-slate-300 pl-2">
            <li>Applying independent professional judgment before acting on any system output.</li>
            <li>Not treating prediction results as guaranteed, verified, or legally actionable conclusions.</li>
            <li>Ensuring that demonstration data and synthetic outputs are not misrepresented as real intelligence.</li>
            <li>Reporting any technical issues or unexpected behaviors observed during demonstration sessions to the project team.</li>
            <li>Maintaining awareness of the prototype's limitations as described in these terms and in the system documentation.</li>
          </ul>
        </Section>

        <Section icon={ShieldCheck} title="8. Intellectual Property">
          <p>
            All source code, user interface designs, architecture documents, data schemas, and conceptual
            frameworks developed for CyberCast represent original work created by the participating project
            team for the Smart India Hackathon competition. This work is subject to competition rules and the
            open-source software licenses of all third-party libraries used, including but not limited to
            React, Vite, FastAPI, Leaflet, scikit-learn, and OpenStreetMap.
          </p>
          <p>
            No part of CyberCast may be used, reproduced, or adapted for commercial purposes without
            appropriate acknowledgment and permission from the project team.
          </p>
        </Section>

        <Section icon={Scale} title="9. Limitation of Liability">
          <p>
            The CyberCast prototype software is provided on an "as is" basis, without warranties of any kind,
            either express or implied. To the fullest extent permissible, the development team shall not be
            liable for any direct, indirect, incidental, special, consequential, or punitive damages resulting
            from:
          </p>
          <ul className="list-disc list-inside space-y-1 text-slate-300 pl-2">
            <li>Use of or reliance on prediction outputs, risk scores, or alerts generated by the system.</li>
            <li>Inability to access or use the prototype for any reason.</li>
            <li>Errors, omissions, or inaccuracies in model outputs or displayed data.</li>
            <li>Any action taken or not taken based on system outputs.</li>
          </ul>
        </Section>

        <Section icon={RefreshCw} title="10. Changes to These Terms">
          <p>
            These Terms and Conditions may be updated as the CyberCast prototype evolves during the
            evaluation period. Material changes will be reflected in the effective date shown at the top of
            this document. Continued use of the prototype following any changes constitutes acceptance of the
            revised terms.
          </p>
        </Section>

        <Section icon={Mail} title="11. Contact">
          <p>
            For questions, clarifications, or feedback regarding these Terms and Conditions or the CyberCast
            prototype in general, please contact the project team at:
          </p>
          <p className="font-mono text-indigo-300 mt-1">
            [Project contact email]
          </p>
        </Section>

      </div>
    </div>
  );
};
