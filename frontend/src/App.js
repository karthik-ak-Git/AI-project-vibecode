import React, { useState, useEffect } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import axios from "axios";
import { Button } from "./components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./components/ui/card";
import { Textarea } from "./components/ui/textarea";
import { Badge } from "./components/ui/badge";
import { Progress } from "./components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import { Separator } from "./components/ui/separator";
import { ScrollArea } from "./components/ui/scroll-area";
import { 
  Zap, 
  Code, 
  Database, 
  Palette, 
  Brain, 
  CheckCircle, 
  Clock, 
  Download,
  Sparkles,
  Layers,
  Settings,
  Play,
  FileCode,
  Globe
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Agent status types
const AGENT_STATUS = {
  WAITING: 'waiting',
  RUNNING: 'running', 
  COMPLETED: 'completed',
  ERROR: 'error'
};

const agents = [
  {
    id: 'designer',
    name: 'Designer Agent',
    description: 'Creates responsive UI layouts with Tailwind CSS',
    icon: Palette,
    color: 'from-pink-500 to-rose-500'
  },
  {
    id: 'frontend',
    name: 'Frontend Agent', 
    description: 'Generates React/Next.js components and logic',
    icon: Code,
    color: 'from-blue-500 to-cyan-500'
  },
  {
    id: 'backend',
    name: 'Backend Agent',
    description: 'Sets up FastAPI/Express.js API endpoints',
    icon: Settings,
    color: 'from-green-500 to-emerald-500'
  },
  {
    id: 'database',
    name: 'Database Agent',
    description: 'Designs MongoDB/PostgreSQL schemas',
    icon: Database,
    color: 'from-purple-500 to-violet-500'
  },
  {
    id: 'ai',
    name: 'AI Service Agent',
    description: 'Integrates AI capabilities and endpoints',
    icon: Brain,
    color: 'from-orange-500 to-red-500'
  },
  {
    id: 'tester',
    name: 'Prompt Tester Agent',
    description: 'Validates and tests generated code',
    icon: CheckCircle,
    color: 'from-teal-500 to-green-500'
  }
];

const Home = () => {
  const [prompt, setPrompt] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [agentStatuses, setAgentStatuses] = useState({});
  const [generatedProject, setGeneratedProject] = useState(null);
  const [currentStep, setCurrentStep] = useState(0);

  // Initialize agent statuses
  useEffect(() => {
    const initialStatuses = {};
    agents.forEach(agent => {
      initialStatuses[agent.id] = {
        status: AGENT_STATUS.WAITING,
        progress: 0,
        result: null,
        logs: []
      };
    });
    setAgentStatuses(initialStatuses);
  }, []);

  const simulateAgentProgress = (agentId) => {
    // Start agent
    setAgentStatuses(prev => ({
      ...prev,
      [agentId]: { ...prev[agentId], status: AGENT_STATUS.RUNNING, progress: 0 }
    }));

    // Simulate progress visually while API processes
    const progressInterval = setInterval(() => {
      setAgentStatuses(prev => {
        const currentProgress = prev[agentId]?.progress || 0;
        if (currentProgress < 90) {
          return {
            ...prev,
            [agentId]: { ...prev[agentId], progress: currentProgress + 10 }
          };
        }
        return prev;
      });
    }, 200);

    return progressInterval;
  };

  const completeAgent = (agentId, result) => {
    setAgentStatuses(prev => ({
      ...prev,
      [agentId]: { 
        ...prev[agentId], 
        status: AGENT_STATUS.COMPLETED, 
        progress: 100,
        result: result
      }
    }));
  };

  const handleGenerate = async () => {
    if (!prompt.trim()) return;
    
    setIsGenerating(true);
    setCurrentStep(0);
    setGeneratedProject(null);
    
    try {
      // Reset all agent statuses
      const resetStatuses = {};
      agents.forEach(agent => {
        resetStatuses[agent.id] = {
          status: AGENT_STATUS.WAITING,
          progress: 0,
          result: null,
          logs: []
        };
      });
      setAgentStatuses(resetStatuses);

      // Start visual progress for all agents
      const progressIntervals = {};
      agents.forEach(agent => {
        progressIntervals[agent.id] = simulateAgentProgress(agent.id);
      });

      // Make actual API call to generate the app
      const response = await axios.post(`${API}/generate`, {
        prompt: prompt.trim()
      });

      if (response.data.success && response.data.project) {
        const project = response.data.project;
        
        // Complete all agents with real results from backend
        agents.forEach(agent => {
          clearInterval(progressIntervals[agent.id]);
          const agentResult = project.agents_results[agent.id] || {};
          completeAgent(agent.id, agentResult);
        });

        // Set the real generated project
        setGeneratedProject(project);
        setCurrentStep(agents.length);

      } else {
        throw new Error('Invalid response from server');
      }

    } catch (error) {
      console.error('Generation failed:', error);
      
      // Mark all running agents as failed
      agents.forEach(agent => {
        setAgentStatuses(prev => ({
          ...prev,
          [agent.id]: { 
            ...prev[agent.id], 
            status: AGENT_STATUS.ERROR, 
            progress: 0
          }
        }));
      });

      // Show user-friendly error message
      alert('App generation failed. Please check your connection and try again.');
      
    } finally {
      setIsGenerating(false);
    }
  };

  const handleExport = async (projectId) => {
    try {
      const response = await axios.post(`${API}/export/${projectId}`);
      
      if (response.data.success && response.data.export_data) {
        const exportData = response.data.export_data;
        
        // Create a downloadable JSON file with the export data
        const dataStr = JSON.stringify(exportData, null, 2);
        const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
        
        const exportFileDefaultName = `${exportData.project_name}-export.json`;
        
        const linkElement = document.createElement('a');
        linkElement.setAttribute('href', dataUri);
        linkElement.setAttribute('download', exportFileDefaultName);
        linkElement.click();
        
        alert('Project exported successfully!');
      } else {
        throw new Error('Export failed');
      }
    } catch (error) {
      console.error('Export failed:', error);
      alert('Export failed. Please try again.');
    }
  };

  const extractProjectName = (prompt) => {
    const words = prompt.toLowerCase().split(' ');
    const appWords = words.filter(word => 
      !['a', 'an', 'the', 'for', 'to', 'build', 'create', 'make', 'app', 'application'].includes(word)
    );
    return appWords.slice(0, 2).join('-') + '-app';
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case AGENT_STATUS.RUNNING:
        return <Clock className="h-4 w-4 animate-spin" />;
      case AGENT_STATUS.COMPLETED:
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case AGENT_STATUS.ERROR:
        return <CheckCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Clock className="h-4 w-4 text-gray-400" />;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Hero Section */}
      <div className="relative overflow-hidden bg-white">
        <div className="absolute inset-0 bg-gradient-to-r from-blue-600/10 to-purple-600/10" />
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24">
          <div className="text-center">
            <div className="flex justify-center mb-8">
              <img 
                src="https://images.unsplash.com/photo-1674027444485-cec3da58eef4?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1Nzl8MHwxfHNlYXJjaHwyfHxhcnRpZmljaWFsJTIwaW50ZWxsaWdlbmNlfGVufDB8fHx8MTc1NjE4OTA2OHww&ixlib=rb-4.1.0&q=85"
                alt="AI Network"
                className="w-32 h-32 rounded-2xl object-cover shadow-2xl"
              />
            </div>
            <h1 className="text-5xl font-bold text-gray-900 mb-6">
              Multi-Agent App Generator
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-purple-600"> Platform</span>
            </h1>
            <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto leading-relaxed">
              Transform your ideas into production-ready web applications using intelligent AI agents. 
              Simply describe what you want to build, and our specialized agents will orchestrate the entire development process.
            </p>
            <div className="flex justify-center space-x-8 text-sm text-gray-500">
              <div className="flex items-center">
                <Sparkles className="h-4 w-4 mr-2" />
                AI-Powered
              </div>
              <div className="flex items-center">
                <Layers className="h-4 w-4 mr-2" />
                Multi-Agent
              </div>
              <div className="flex items-center">
                <Globe className="h-4 w-4 mr-2" />
                Production Ready
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Left Panel - Input */}
          <div className="lg:col-span-1">
            <Card className="sticky top-8">
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Zap className="h-5 w-5 mr-2 text-yellow-500" />
                  Describe Your App
                </CardTitle>
                <CardDescription>
                  Tell us what kind of application you want to build
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <Textarea
                  placeholder="e.g., Build a task management app with user authentication, project boards, real-time collaboration, and deadline tracking..."
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  rows={6}
                  className="resize-none"
                />
                <Button 
                  onClick={handleGenerate}
                  disabled={!prompt.trim() || isGenerating}
                  className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
                  size="lg"
                >
                  {isGenerating ? (
                    <>
                      <Clock className="h-4 w-4 mr-2 animate-spin" />
                      Generating...
                    </>
                  ) : (
                    <>
                      <Play className="h-4 w-4 mr-2" />
                      Generate App
                    </>
                  )}
                </Button>
                
                {isGenerating && (
                  <div className="text-center">
                    <div className="text-sm text-gray-600 mb-2">
                      Step {currentStep} of {agents.length}
                    </div>
                    <Progress value={(currentStep / agents.length) * 100} className="w-full" />
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Right Panel - Agents & Results */}
          <div className="lg:col-span-2 space-y-8">
            
            {/* Agents Grid */}
            <div>
              <h2 className="text-2xl font-bold text-gray-900 mb-6">AI Agents</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {agents.map((agent) => {
                  const status = agentStatuses[agent.id] || {};
                  const IconComponent = agent.icon;
                  
                  return (
                    <Card key={agent.id} className="transition-all duration-200 hover:shadow-md">
                      <CardContent className="p-4">
                        <div className="flex items-start space-x-3">
                          <div className={`p-2 rounded-lg bg-gradient-to-r ${agent.color}`}>
                            <IconComponent className="h-5 w-5 text-white" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center space-x-2 mb-1">
                              <h3 className="font-semibold text-gray-900 truncate">
                                {agent.name}
                              </h3>
                              {getStatusIcon(status.status)}
                            </div>
                            <p className="text-sm text-gray-600 mb-2">
                              {agent.description}
                            </p>
                            {status.status === AGENT_STATUS.RUNNING && (
                              <Progress value={status.progress} className="h-2" />
                            )}
                            {status.status === AGENT_STATUS.COMPLETED && (
                              <Badge variant="secondary" className="text-green-700 bg-green-100">
                                Completed
                              </Badge>
                            )}
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            </div>

            {/* Generated Project */}
            {generatedProject && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <div className="flex items-center">
                      <FileCode className="h-5 w-5 mr-2" />
                      Generated Project: {generatedProject.name}
                    </div>
                    <Button variant="outline" size="sm">
                      <Download className="h-4 w-4 mr-2" />
                      Export
                    </Button>
                  </CardTitle>
                  <CardDescription>
                    {generatedProject.description}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <Tabs defaultValue="structure" className="w-full">
                    <TabsList className="grid w-full grid-cols-3">
                      <TabsTrigger value="structure">File Structure</TabsTrigger>
                      <TabsTrigger value="technologies">Technologies</TabsTrigger>
                      <TabsTrigger value="agents">Agent Results</TabsTrigger>
                    </TabsList>
                    
                    <TabsContent value="structure" className="space-y-4">
                      <ScrollArea className="h-64 w-full rounded border p-4">
                        {Object.entries(generatedProject.structure).map(([folder, files]) => (
                          <div key={folder} className="mb-4">
                            <h4 className="font-semibold text-gray-900 mb-2 capitalize">
                              {folder}/
                            </h4>
                            {files.map((file, index) => (
                              <div key={index} className="text-sm text-gray-600 ml-4 mb-1">
                                📄 {file}
                              </div>
                            ))}
                          </div>
                        ))}
                      </ScrollArea>
                    </TabsContent>
                    
                    <TabsContent value="technologies" className="space-y-4">
                      <div className="flex flex-wrap gap-2">
                        {generatedProject.technologies.map((tech, index) => (
                          <Badge key={index} variant="outline" className="text-blue-700 border-blue-200">
                            {tech}
                          </Badge>
                        ))}
                      </div>
                    </TabsContent>
                    
                    <TabsContent value="agents" className="space-y-4">
                      {agents.map((agent) => {
                        const result = agentStatuses[agent.id]?.result;
                        if (!result) return null;
                        
                        return (
                          <div key={agent.id} className="border rounded-lg p-4">
                            <h4 className="font-semibold text-gray-900 mb-2">
                              {agent.name} Output
                            </h4>
                            <div className="text-sm text-gray-600 space-y-1">
                              {Object.entries(result).map(([key, value]) => (
                                <div key={key}>
                                  <span className="font-medium capitalize">{key}:</span>{' '}
                                  {Array.isArray(value) ? value.join(', ') : value}
                                </div>
                              ))}
                            </div>
                          </div>
                        );
                      })}
                    </TabsContent>
                  </Tabs>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;