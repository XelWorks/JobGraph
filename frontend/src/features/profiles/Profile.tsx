import React, { useState, useEffect, useRef } from 'react';
import {
  User,
  Sparkles,
  Phone,
  Briefcase,
  MapPin,
  DollarSign,
  AlertCircle,
  CheckCircle2,
  UploadCloud,
  FileText,
  Lock,
  Plus,
  X
} from 'lucide-react';

interface ProfileProps {
  token: string;
}

export const Profile: React.FC<ProfileProps> = ({ token }) => {
  const [phone, setPhone] = useState('');
  const [preferredRoles, setPreferredRoles] = useState<string[]>([]);
  const [preferredLocations, setPreferredLocations] = useState<string[]>([]);
  const [targetSalary, setTargetSalary] = useState<number>(0);
  const [skills, setSkills] = useState<string[]>([]);
  const [masterResumeUrl, setMasterResumeUrl] = useState<string | null>(null);

  // Form input temporary fields
  const [newRole, setNewRole] = useState('');
  const [newLocation, setNewLocation] = useState('');
  const [newSkill, setNewSkill] = useState('');

  // UI state managers
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // File Upload states
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const meta = import.meta as unknown as { env?: { VITE_API_URL?: string } };
  const apiUrl = meta.env?.VITE_API_URL || 'http://localhost:8000';

  useEffect(() => {
    let active = true;
    async function loadProfile() {
      try {
        const response = await fetch(`${apiUrl}/api/v1/profile`, {
          headers: { 'Authorization': `Bearer ${token}` },
        });
        
        if (response.status === 404) {
          // Profile is not initialized yet. Keep initial empty states
          setLoading(false);
          return;
        }

        if (!response.ok) {
          throw new Error('Failed to load profile details.');
        }

        const data = await response.json();
        if (active) {
          setPhone(data.phone || '');
          setPreferredRoles(data.preferred_roles || []);
          setPreferredLocations(data.preferred_locations || []);
          setTargetSalary(data.target_salary || 0);
          setSkills(data.skills || []);
          setMasterResumeUrl(data.master_resume_url || null);
          setLoading(false);
        }
      } catch (err: unknown) {
        if (active) {
          const errMsg = err instanceof Error ? err.message : 'Could not fetch profile configurations.';
          setError(errMsg);
          setLoading(false);
        }
      }
    }

    loadProfile();
    return () => {
      active = false;
    };
  }, [apiUrl, token]);

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setSaving(true);

    if (skills.length === 0) {
      setError('Skills list cannot be empty. Please configure at least one skill.');
      setSaving(false);
      return;
    }

    if (targetSalary < 0) {
      setError('Target salary must be a positive number.');
      setSaving(false);
      return;
    }

    try {
      const response = await fetch(`${apiUrl}/api/v1/profile`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          phone: phone.trim() || null,
          preferred_roles: preferredRoles,
          preferred_locations: preferredLocations,
          target_salary: targetSalary,
          skills: skills
        }),
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || 'Failed to update profile.');
      }

      const data = await response.json();
      setPhone(data.phone || '');
      setPreferredRoles(data.preferred_roles || []);
      setPreferredLocations(data.preferred_locations || []);
      setTargetSalary(data.target_salary || 0);
      setSkills(data.skills || []);
      setMasterResumeUrl(data.master_resume_url || null);
      setSuccess('Profile configuration saved successfully!');
    } catch (err: unknown) {
      const errMsg = err instanceof Error ? err.message : 'An error occurred during save.';
      setError(errMsg);
    } finally {
      setSaving(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const fileList = e.target.files;
    if (!fileList || fileList.length === 0) return;

    const file = fileList[0];
    const ext = file.name.split('.').pop()?.toLowerCase();
    if (!ext || !['pdf', 'docx', 'doc'].includes(ext)) {
      setError('Only PDF or Word documents (.pdf, .docx, .doc) are permitted.');
      return;
    }

    setError(null);
    setSuccess(null);
    setUploading(true);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${apiUrl}/api/v1/profile/resume`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData,
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || 'Resume upload failed.');
      }

      const data = await response.json();
      setMasterResumeUrl(data.master_resume_url);
      setSuccess('Master resume uploaded and synchronized successfully!');
    } catch (err: unknown) {
      const errMsg = err instanceof Error ? err.message : 'Failed to complete file upload.';
      setError(errMsg);
    } finally {
      setUploading(false);
    }
  };

  // List helpers
  const addRole = () => {
    if (newRole.trim() && !preferredRoles.includes(newRole.trim())) {
      setPreferredRoles([...preferredRoles, newRole.trim()]);
      setNewRole('');
    }
  };

  const removeRole = (index: number) => {
    setPreferredRoles(preferredRoles.filter((_, i) => i !== index));
  };

  const addLocation = () => {
    if (newLocation.trim() && !preferredLocations.includes(newLocation.trim())) {
      setPreferredLocations([...preferredLocations, newLocation.trim()]);
      setNewLocation('');
    }
  };

  const removeLocation = (index: number) => {
    setPreferredLocations(preferredLocations.filter((_, i) => i !== index));
  };

  const addSkill = () => {
    if (newSkill.trim() && !skills.includes(newSkill.trim())) {
      setSkills([...skills, newSkill.trim()]);
      setNewSkill('');
    }
  };

  const removeSkill = (index: number) => {
    setSkills(skills.filter((_, i) => i !== index));
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-20 space-y-4">
        <svg className="animate-spin h-8 w-8 text-sky-400" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
        <p className="text-slate-400 text-sm">Loading candidate profile configurations...</p>
      </div>
    );
  }

  return (
    <div className="max-w-4xl space-y-8 animate-fadeIn">
      {/* Page Title */}
      <div className="flex items-center gap-3 border-b border-slate-800 pb-5">
        <User className="h-6 w-6 text-sky-400" />
        <div>
          <h2 className="text-xl font-bold text-white">Candidate Profile</h2>
          <p className="text-xs text-slate-500">Configure your skills, locations, preferred roles, and upload your master resume</p>
        </div>
      </div>

      {/* Alert Feedbacks */}
      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/20 text-rose-400 rounded-xl flex gap-3 text-sm animate-fadeIn">
          <AlertCircle className="h-5 w-5 shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {success && (
        <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded-xl flex gap-3 text-sm animate-fadeIn">
          <CheckCircle2 className="h-5 w-5 shrink-0 mt-0.5" />
          <span>{success}</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Forms Field Section */}
        <form onSubmit={handleSaveProfile} className="lg:col-span-2 space-y-6">
          <div className="bg-slate-950/20 border border-slate-800/60 rounded-2xl p-6 md:p-8 space-y-6">
            <h3 className="text-sm font-bold tracking-wider text-slate-400 uppercase">1. General Information</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Contact Phone */}
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-400 flex items-center gap-1.5">
                  <Phone className="h-3.5 w-3.5 text-slate-500" /> Phone number
                </label>
                <input
                  type="text"
                  placeholder="+1 (555) 019-2834"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  className="w-full bg-slate-900/60 border border-slate-800 hover:border-slate-700/80 focus:border-sky-500/80 rounded-xl px-4 py-2.5 text-sm text-slate-200 outline-none transition-all placeholder:text-slate-600"
                />
              </div>

              {/* Target Salary */}
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-400 flex items-center gap-1.5">
                  <DollarSign className="h-3.5 w-3.5 text-slate-500" /> Target Salary ($ / year)
                </label>
                <input
                  type="number"
                  min="0"
                  value={targetSalary}
                  onChange={(e) => setTargetSalary(Number(e.target.value))}
                  className="w-full bg-slate-900/60 border border-slate-800 hover:border-slate-700/80 focus:border-sky-500/80 rounded-xl px-4 py-2.5 text-sm text-slate-200 outline-none transition-all placeholder:text-slate-600"
                />
              </div>
            </div>
          </div>

          <div className="bg-slate-950/20 border border-slate-800/60 rounded-2xl p-6 md:p-8 space-y-6">
            <h3 className="text-sm font-bold tracking-wider text-slate-400 uppercase">2. Targets & Skills</h3>

            {/* Preferred Roles List */}
            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-400 flex items-center gap-1.5">
                <Briefcase className="h-3.5 w-3.5 text-slate-500" /> Preferred Roles
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder="e.g. Backend Engineer"
                  value={newRole}
                  onChange={(e) => setNewRole(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addRole())}
                  className="flex-1 bg-slate-900/60 border border-slate-800 focus:border-sky-500/80 rounded-xl px-4 py-2 text-sm text-slate-200 outline-none transition-all"
                />
                <button
                  type="button"
                  onClick={addRole}
                  className="p-2.5 bg-slate-900 border border-slate-800 hover:border-slate-700 rounded-xl text-sky-400 hover:bg-slate-850 transition-all focus:outline-none"
                >
                  <Plus className="h-5 w-5" />
                </button>
              </div>
              <div className="flex flex-wrap gap-1.5 pt-1">
                {preferredRoles.map((role, i) => (
                  <span key={i} className="inline-flex items-center gap-1 text-xs font-medium px-2.5 py-1 rounded-lg bg-sky-500/10 border border-sky-500/20 text-sky-300">
                    {role}
                    <button type="button" onClick={() => removeRole(i)} className="hover:text-sky-100 focus:outline-none">
                      <X className="h-3 w-3" />
                    </button>
                  </span>
                ))}
              </div>
            </div>

            {/* Preferred Locations List */}
            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-400 flex items-center gap-1.5">
                <MapPin className="h-3.5 w-3.5 text-slate-500" /> Preferred Locations
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder="e.g. Remote"
                  value={newLocation}
                  onChange={(e) => setNewLocation(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addLocation())}
                  className="flex-1 bg-slate-900/60 border border-slate-800 focus:border-sky-500/80 rounded-xl px-4 py-2 text-sm text-slate-200 outline-none transition-all"
                />
                <button
                  type="button"
                  onClick={addLocation}
                  className="p-2.5 bg-slate-900 border border-slate-800 hover:border-slate-700 rounded-xl text-sky-400 hover:bg-slate-850 transition-all focus:outline-none"
                >
                  <Plus className="h-5 w-5" />
                </button>
              </div>
              <div className="flex flex-wrap gap-1.5 pt-1">
                {preferredLocations.map((loc, i) => (
                  <span key={i} className="inline-flex items-center gap-1 text-xs font-medium px-2.5 py-1 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-300">
                    {loc}
                    <button type="button" onClick={() => removeLocation(i)} className="hover:text-indigo-100 focus:outline-none">
                      <X className="h-3 w-3" />
                    </button>
                  </span>
                ))}
              </div>
            </div>

            {/* Core Skills List */}
            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-400 flex items-center gap-1.5">
                <Sparkles className="h-3.5 w-3.5 text-slate-500" /> Core Skills <span className="text-rose-500">*</span>
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder="e.g. FastAPI"
                  value={newSkill}
                  onChange={(e) => setNewSkill(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addSkill())}
                  className="flex-1 bg-slate-900/60 border border-slate-800 focus:border-sky-500/80 rounded-xl px-4 py-2 text-sm text-slate-200 outline-none transition-all"
                />
                <button
                  type="button"
                  onClick={addSkill}
                  className="p-2.5 bg-slate-900 border border-slate-800 hover:border-slate-700 rounded-xl text-sky-400 hover:bg-slate-850 transition-all focus:outline-none"
                >
                  <Plus className="h-5 w-5" />
                </button>
              </div>
              <div className="flex flex-wrap gap-1.5 pt-1">
                {skills.map((skill, i) => (
                  <span key={i} className="inline-flex items-center gap-1 text-xs font-medium px-2.5 py-1 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-300">
                    {skill}
                    <button type="button" onClick={() => removeSkill(i)} className="hover:text-emerald-100 focus:outline-none">
                      <X className="h-3 w-3" />
                    </button>
                  </span>
                ))}
              </div>
            </div>
          </div>

          <button
            type="submit"
            disabled={saving}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-gradient-to-r from-sky-500 to-indigo-500 hover:from-sky-400 hover:to-indigo-400 text-white font-bold text-sm shadow-[0_0_15px_-3px_rgba(14,165,233,0.3)] transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none"
          >
            {saving ? 'Saving Configurations...' : 'Save Profile Settings'}
          </button>
        </form>

        {/* Object Storage File Upload Card */}
        <div className="space-y-6">
          <div className="bg-slate-950/20 border border-slate-800/60 rounded-2xl p-6 space-y-6">
            <h3 className="text-sm font-bold tracking-wider text-slate-400 uppercase">3. Document Upload</h3>

            <div className="space-y-4">
              <label className="text-xs font-semibold text-slate-400 flex items-center gap-1.5">
                <FileText className="h-3.5 w-3.5 text-slate-500" /> Master Resume (.pdf, .docx)
              </label>

              {/* Upload Dropzone */}
              <div
                onClick={() => fileInputRef.current?.click()}
                className="border-2 border-dashed border-slate-800 hover:border-slate-700/80 bg-slate-900/10 hover:bg-slate-900/20 rounded-xl p-6 text-center cursor-pointer transition-all duration-200 group"
              >
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleFileUpload}
                  accept=".pdf,.docx,.doc"
                  className="hidden"
                />
                
                {uploading ? (
                  <div className="flex flex-col items-center py-4 space-y-3">
                    <svg className="animate-spin h-6 w-6 text-sky-400" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    <span className="text-xs text-slate-400">Uploading payload to MinIO...</span>
                  </div>
                ) : (
                  <div className="py-4 space-y-2">
                    <UploadCloud className="h-8 w-8 text-slate-500 group-hover:text-sky-400 mx-auto transition-colors" />
                    <p className="text-xs font-medium text-slate-300">Click to upload resume</p>
                    <p className="text-[10px] text-slate-500">Supports PDF or Word documents up to 5MB</p>
                  </div>
                )}
              </div>

              {/* Active Document Card */}
              {masterResumeUrl && (
                <div className="p-4 bg-slate-900/40 border border-slate-800/80 rounded-xl flex items-center justify-between gap-3 animate-fadeIn">
                  <div className="min-w-0 flex-1 flex items-center gap-2.5">
                    <FileText className="h-5 w-5 text-sky-400 shrink-0" />
                    <div className="min-w-0 flex-1">
                      <p className="text-xs font-semibold text-slate-200 truncate">master_resume_version.pdf</p>
                      <p className="text-[10px] text-emerald-400 flex items-center gap-1 mt-0.5">
                        <CheckCircle2 className="h-3 w-3" /> Live pre-signed link
                      </p>
                    </div>
                  </div>
                  <a
                    href={masterResumeUrl}
                    target="_blank"
                    rel="noreferrer"
                    className="p-2 text-slate-400 hover:text-sky-400 bg-slate-950/40 hover:bg-slate-950/90 rounded-lg border border-slate-800 transition-all text-xs font-medium"
                  >
                    View
                  </a>
                </div>
              )}
            </div>
          </div>

          {/* Privacy Notice */}
          <div className="bg-sky-500/5 border border-sky-500/10 rounded-2xl p-6 flex gap-3.5">
            <Lock className="h-5 w-5 text-sky-400 shrink-0 mt-0.5" />
            <div className="text-xs leading-normal">
              <h4 className="font-semibold text-sky-300 mb-1">Local Sandbox Mode</h4>
              <p className="text-slate-400">
                Resumes uploaded here are securely persisted within your local, offline MinIO S3 bucket, protecting credentials and sensitive personal records.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
