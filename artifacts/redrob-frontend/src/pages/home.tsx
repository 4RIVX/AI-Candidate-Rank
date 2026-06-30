import React, { useState, useRef } from "react";
import { useGetRankingStatus } from "@workspace/api-client-react";
import { Slider } from "@/components/ui/slider";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Progress } from "@/components/ui/progress";
import { UploadCloud, FileJson, Loader2, Download, AlertCircle, Trophy, Medal, Award, MapPin, Briefcase, Zap } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { useToast } from "@/hooks/use-toast";

type RankedCandidate = {
  rank: number;
  candidate_id: string;
  current_title: string | null;
  current_company: string | null;
  years_of_experience: number | null;
  location: string | null;
  willing_to_relocate: boolean | null;
  score: number;
  scores: {
    semantic: number;
    experience: number;
    skill: number;
    behavioral: number;
    final: number;
    disqualifier_multiplier: number;
    disqualifier_flag: string | null;
  };
  reasoning: string;
};

type ScoreBucket = {
  range: string;
  count: number;
};

type RankStats = {
  profiles_loaded: number;
  candidates_ranked: number;
  top_score: number;
  disqualified_count: number;
  score_distribution: ScoreBucket[];
};

type RankResponse = {
  candidates: RankedCandidate[];
  stats: RankStats;
  processing_time_seconds: number;
};

export default function Home() {
  const { toast } = useToast();
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const [candidates, setCandidates] = useState<any[]>([]);
  const [fileName, setFileName] = useState<string | null>(null);
  const [fileSize, setFileSize] = useState<number | null>(null);
  const [topN, setTopN] = useState<number>(25);
  
  const [isRanking, setIsRanking] = useState(false);
  const [rankResult, setRankResult] = useState<RankResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const { data: status } = useGetRankingStatus({ query: { refetchInterval: 5000, queryKey: ['rankingStatus'] } });

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setFileName(file.name);
    setFileSize(file.size);
    setError(null);
    setRankResult(null);

    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const text = event.target?.result as string;
        let parsed: any[];
        if (text.trim().startsWith('[')) {
          parsed = JSON.parse(text);
        } else {
          parsed = text.trim().split('\n').filter(Boolean).map(line => JSON.parse(line));
        }
        setCandidates(parsed);
      } catch (err) {
        setError("Failed to parse file. Please ensure it is valid JSON or JSONL.");
        setCandidates([]);
      }
    };
    reader.onerror = () => {
      setError("Failed to read file.");
    };
    reader.readAsText(file);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      if (fileInputRef.current) {
        fileInputRef.current.files = e.dataTransfer.files;
        handleFileUpload({ target: fileInputRef.current } as any);
      }
    }
  };

  const rankCandidates = async () => {
    if (!candidates.length) {
      toast({ title: "No candidates loaded", description: "Please upload a file first.", variant: "destructive" });
      return;
    }
    
    setIsRanking(true);
    setError(null);
    try {
      const response = await fetch('/api/rank', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ candidates, top_n: topN })
      });
      
      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.error || `HTTP error ${response.status}`);
      }
      
      const data: RankResponse = await response.json();
      setRankResult(data);
    } catch (err: any) {
      setError(err.message || "Failed to rank candidates");
    } finally {
      setIsRanking(false);
    }
  };

  const downloadCSV = async () => {
    try {
      const csvResp = await fetch('/api/rank/download', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ candidates, top_n: topN })
      });
      if (!csvResp.ok) throw new Error("Failed to download CSV");
      const blob = await csvResp.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url; 
      a.download = 'ranked_candidates.csv'; 
      a.click();
      URL.revokeObjectURL(url);
    } catch (err: any) {
      toast({ title: "Download Failed", description: err.message, variant: "destructive" });
    }
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="flex h-screen w-full bg-background text-foreground overflow-hidden font-sans">
      {/* Sidebar */}
      <div className="w-80 border-r border-border bg-sidebar flex flex-col shrink-0 relative z-10">
        <div className="p-6 border-b border-border">
          <div className="flex items-center gap-2 mb-3">
            <Zap className="h-6 w-6 text-primary" />
            <h1 className="text-xl font-bold tracking-tight text-white">AI CANDIDATE RANKER</h1>
          </div>
          <div className="flex items-center gap-2 px-3 py-2 rounded-md bg-primary/10 border border-primary/30">
            <Briefcase className="h-3.5 w-3.5 text-primary shrink-0" />
            <span className="text-[11px] font-semibold text-primary leading-tight">Matching for: Senior AI Engineer — Redrob AI (Pune/Noida)</span>
          </div>
        </div>

        <div className="p-6 flex-1 flex flex-col gap-6 overflow-y-auto">
          {/* Engine Status */}
          <div className="flex items-center gap-2 p-3 bg-card border border-border rounded-md">
            <div className={`h-2.5 w-2.5 rounded-full ${status?.model_loaded ? 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]' : 'bg-yellow-500 shadow-[0_0_8px_rgba(234,179,8,0.6)]'}`} />
            <div className="flex flex-col">
              <span className="text-xs font-semibold uppercase tracking-wider">{status?.model_loaded ? 'ENGINE ONLINE' : 'ENGINE WAKING UP'}</span>
              <span className="text-[10px] text-muted-foreground">{status?.message || 'Initializing model...'}</span>
            </div>
          </div>

          {/* Upload Area */}
          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Candidate Data</label>
            <div 
              className={`border-2 border-dashed rounded-lg p-6 flex flex-col items-center justify-center gap-2 transition-colors cursor-pointer text-center ${fileName ? 'border-primary/50 bg-primary/5' : 'border-border hover:border-primary/50 hover:bg-muted/50'}`}
              onDragOver={handleDragOver}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
            >
              <input type="file" ref={fileInputRef} className="hidden" accept=".json,.jsonl" onChange={handleFileUpload} />
              {fileName ? (
                <>
                  <FileJson className="h-8 w-8 text-primary mb-1" />
                  <div className="text-sm font-medium text-foreground break-all">{fileName}</div>
                  <div className="text-xs text-muted-foreground">{formatBytes(fileSize || 0)} • {candidates.length} profiles</div>
                </>
              ) : (
                <>
                  <UploadCloud className="h-8 w-8 text-muted-foreground mb-1" />
                  <div className="text-sm font-medium">Drop JSON or JSONL file here</div>
                  <div className="text-xs text-muted-foreground">or click to browse</div>
                </>
              )}
            </div>
          </div>

          {/* Slider */}
          <div className="space-y-4 pt-4 border-t border-border">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Top N to display</label>
              <span className="text-xs font-mono font-medium text-primary">{topN}</span>
            </div>
            <Slider
              value={[topN]}
              onValueChange={(v) => setTopN(v[0])}
              max={100}
              min={10}
              step={5}
              className="py-2"
            />
          </div>

          {/* Action */}
          <div className="mt-auto pt-6">
            <Button 
              className="w-full h-12 text-base font-bold bg-gradient-to-r from-primary to-accent hover:from-primary/90 hover:to-accent/90 text-white shadow-lg border-0 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
              onClick={rankCandidates}
              disabled={!candidates.length || isRanking}
              data-testid="button-rank-candidates"
            >
              {isRanking ? (
                <>
                  <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                  Processing...
                </>
              ) : (
                "Rank Candidates"
              )}
            </Button>
            {error && (
              <div className="mt-3 p-3 bg-destructive/10 border border-destructive/20 rounded text-xs text-destructive flex items-start gap-2">
                <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
                <span className="leading-tight">{error}</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Main Panel */}
      <div className="flex-1 flex flex-col bg-background relative overflow-hidden">
        {!rankResult && !isRanking ? (
          <div className="flex-1 flex flex-col items-center justify-center p-8 text-center opacity-50">
            <div className="w-24 h-24 mb-6 rounded-full bg-muted flex items-center justify-center">
              <Zap className="h-10 w-10 text-muted-foreground" />
            </div>
            <h2 className="text-2xl font-bold mb-2">Awaiting Telemetry</h2>
            <p className="text-muted-foreground max-w-md">
              Upload candidate profiles in the sidebar and initiate ranking sequence. 
              The engine will score across semantic matching, experience, skills, and behavioral signals.
            </p>
          </div>
        ) : isRanking ? (
          <div className="flex-1 flex flex-col items-center justify-center p-8">
            <div className="relative">
              <div className="w-32 h-32 border-4 border-muted rounded-full absolute top-0 left-0" />
              <div className="w-32 h-32 border-4 border-primary border-t-transparent rounded-full animate-spin relative z-10" />
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="font-mono text-xl font-bold text-primary animate-pulse">ML</span>
              </div>
            </div>
            <h3 className="mt-8 text-xl font-bold tracking-widest uppercase">Analyzing Data...</h3>
            <p className="mt-2 text-muted-foreground font-mono text-sm">Evaluating multi-dimensional vectors</p>
          </div>
        ) : (
          <ScrollArea className="flex-1 p-8">
            <div className="max-w-6xl mx-auto space-y-8 pb-12 animate-in fade-in slide-in-from-bottom-4 duration-500">
              
              {/* Header row */}
              <div className="flex items-end justify-between">
                <div>
                  <h2 className="text-2xl font-bold">Analysis Complete</h2>
                  <p className="text-sm text-muted-foreground font-mono mt-1">Processed in {rankResult!.processing_time_seconds.toFixed(2)}s</p>
                </div>
                <Button variant="outline" onClick={downloadCSV} className="gap-2 font-mono text-xs">
                  <Download className="h-4 w-4" />
                  Export CSV
                </Button>
              </div>

              {/* Stats Row */}
              <div className="grid grid-cols-4 gap-4">
                <Card className="bg-card/50 border-border/50">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Profiles Loaded</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-mono font-bold text-white">{rankResult!.stats.profiles_loaded}</div>
                  </CardContent>
                </Card>
                <Card className="bg-card/50 border-border/50">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Ranked</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-mono font-bold text-primary">{rankResult!.stats.candidates_ranked}</div>
                  </CardContent>
                </Card>
                <Card className="bg-card/50 border-border/50">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Top Score</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-mono font-bold text-white">{(rankResult!.stats.top_score * 100).toFixed(1)}<span className="text-xl text-muted-foreground">%</span></div>
                  </CardContent>
                </Card>
                <Card className="bg-card/50 border-border/50">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Disqualified</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-mono font-bold text-destructive">{rankResult!.stats.disqualified_count}</div>
                  </CardContent>
                </Card>
              </div>

              {/* Score Distribution Chart */}
              <Card className="bg-card/30 border-border/50 overflow-hidden">
                <CardHeader className="py-4 border-b border-border/30">
                  <CardTitle className="text-sm font-semibold uppercase tracking-wider">Score Distribution</CardTitle>
                </CardHeader>
                <CardContent className="pt-6 pb-2 h-[200px] w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={rankResult!.stats.score_distribution} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" vertical={false} />
                      <XAxis dataKey="range" tick={{ fontSize: 10, fill: '#ffffff60' }} axisLine={false} tickLine={false} />
                      <YAxis tick={{ fontSize: 10, fill: '#ffffff60' }} axisLine={false} tickLine={false} />
                      <Tooltip 
                        cursor={{ fill: '#ffffff05' }}
                        contentStyle={{ backgroundColor: 'hsl(var(--card))', border: '1px solid hsl(var(--border))', borderRadius: '4px', fontSize: '12px' }}
                      />
                      <Bar dataKey="count" fill="hsl(var(--primary))" radius={[2, 2, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              {/* Ranked Candidates */}
              <div className="space-y-4">
                <h3 className="text-lg font-bold">Top Candidates</h3>
                <div className="space-y-3">
                  {rankResult!.candidates.map((candidate, i) => (
                    <CandidateCard key={candidate.candidate_id} candidate={candidate} index={i} />
                  ))}
                </div>
              </div>

            </div>
          </ScrollArea>
        )}
      </div>
    </div>
  );
}

function CandidateCard({ candidate, index }: { candidate: RankedCandidate, index: number }) {
  const isTop3 = index < 3;
  
  const getRankBadge = () => {
    if (index === 0) return <Badge className="bg-yellow-500 hover:bg-yellow-600 text-yellow-950 font-bold px-2 py-1"><Trophy className="w-3 h-3 mr-1" /> #1</Badge>;
    if (index === 1) return <Badge className="bg-slate-300 hover:bg-slate-400 text-slate-900 font-bold px-2 py-1"><Medal className="w-3 h-3 mr-1" /> #2</Badge>;
    if (index === 2) return <Badge className="bg-amber-700 hover:bg-amber-800 text-amber-100 font-bold px-2 py-1"><Award className="w-3 h-3 mr-1" /> #3</Badge>;
    return <Badge variant="outline" className="font-mono text-muted-foreground border-muted-foreground/30">#{index + 1}</Badge>;
  };

  return (
    <div className={`p-5 rounded-lg border ${isTop3 ? 'bg-card border-primary/20 shadow-[0_4px_24px_-12px_rgba(255,150,0,0.15)]' : 'bg-card/50 border-border/50 hover:bg-card hover:border-border transition-colors'} flex flex-col gap-4 relative group`}>
      <div className="flex items-start justify-between gap-4">
        <div className="flex gap-4">
          <div className="mt-1">{getRankBadge()}</div>
          <div>
            <div className="flex items-center gap-2">
              <h4 className="font-bold text-lg text-white">ID: {candidate.candidate_id.split('-')[0]}...</h4>
              {candidate.scores.disqualifier_flag && (
                <Badge variant="destructive" className="text-[10px] h-5 px-1.5 uppercase font-bold tracking-wider">
                  {candidate.scores.disqualifier_flag}
                </Badge>
              )}
            </div>
            
            <div className="flex items-center gap-4 mt-1.5 text-sm text-muted-foreground">
              {candidate.current_title && (
                <div className="flex items-center gap-1.5">
                  <Briefcase className="w-3.5 h-3.5" />
                  <span className="text-foreground/80">{candidate.current_title} {candidate.current_company && `at ${candidate.current_company}`}</span>
                </div>
              )}
              {candidate.location && (
                <div className="flex items-center gap-1.5">
                  <MapPin className="w-3.5 h-3.5" />
                  <span>{candidate.location} {candidate.willing_to_relocate && '(Relo OK)'}</span>
                </div>
              )}
              {candidate.years_of_experience !== null && (
                <div className="flex items-center gap-1.5">
                  <span className="font-mono font-medium">{candidate.years_of_experience} YOE</span>
                </div>
              )}
            </div>
          </div>
        </div>
        
        <div className="flex flex-col items-end shrink-0">
          <div className="text-2xl font-mono font-bold text-white flex items-baseline">
            {(candidate.score * 100).toFixed(1)}<span className="text-sm text-muted-foreground ml-0.5">%</span>
          </div>
          <div className="text-[10px] uppercase font-bold tracking-wider text-muted-foreground mt-0.5">Final Score</div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-5 gap-6 border-t border-border/50 pt-4">
        <div className="md:col-span-2 space-y-3">
          <div className="flex items-center justify-between text-xs mb-1">
            <span className="text-muted-foreground font-semibold">Semantic Match</span>
            <span className="font-mono text-white">{(candidate.scores.semantic * 100).toFixed(0)}%</span>
          </div>
          <div className="h-1.5 w-full bg-muted rounded-full overflow-hidden">
            <div className="h-full bg-[hsl(var(--chart-1))] rounded-full" style={{ width: `${candidate.scores.semantic * 100}%` }} />
          </div>
          
          <div className="flex items-center justify-between text-xs mb-1 pt-1">
            <span className="text-muted-foreground font-semibold">Experience</span>
            <span className="font-mono text-white">{(candidate.scores.experience * 100).toFixed(0)}%</span>
          </div>
          <div className="h-1.5 w-full bg-muted rounded-full overflow-hidden">
            <div className="h-full bg-[hsl(var(--chart-2))] rounded-full" style={{ width: `${candidate.scores.experience * 100}%` }} />
          </div>
        </div>
        
        <div className="md:col-span-2 space-y-3">
          <div className="flex items-center justify-between text-xs mb-1">
            <span className="text-muted-foreground font-semibold">Skills</span>
            <span className="font-mono text-white">{(candidate.scores.skill * 100).toFixed(0)}%</span>
          </div>
          <div className="h-1.5 w-full bg-muted rounded-full overflow-hidden">
            <div className="h-full bg-[hsl(var(--chart-3))] rounded-full" style={{ width: `${candidate.scores.skill * 100}%` }} />
          </div>
          
          <div className="flex items-center justify-between text-xs mb-1 pt-1">
            <span className="text-muted-foreground font-semibold">Behavioral</span>
            <span className="font-mono text-white">{(candidate.scores.behavioral * 100).toFixed(0)}%</span>
          </div>
          <div className="h-1.5 w-full bg-muted rounded-full overflow-hidden">
            <div className="h-full bg-[hsl(var(--chart-4))] rounded-full" style={{ width: `${candidate.scores.behavioral * 100}%` }} />
          </div>
        </div>

        <div className="md:col-span-1 border-l border-border/50 pl-6 flex flex-col justify-center">
           <div className="text-xs italic text-muted-foreground leading-relaxed line-clamp-4 group-hover:line-clamp-none transition-all">
             "{candidate.reasoning}"
           </div>
        </div>
      </div>
    </div>
  );
}
