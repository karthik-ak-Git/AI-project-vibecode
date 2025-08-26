import React, { useState, useEffect } from "react";
import { useAuth } from '../../contexts/AuthContext';
import axios from "axios";
import { Button } from "../ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../ui/card";
import { Textarea } from "../ui/textarea";
import { Badge } from "../ui/badge";
import { Progress } from "../ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../ui/tabs";
import { Separator } from "../ui/separator";
import { ScrollArea } from "../ui/scroll-area";
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
  Globe,
  User,
  Briefcase,
  LogOut
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

const UserDashboard = () => {
  const { user, logout } = useAuth();
  const [prompt, setPrompt] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [agentStatuses, setAgentStatuses] = useState({});
  const [generatedProject, setGeneratedProject] = useState(null);
  const [currentStep, setCurrentStep] = useState(0);
  const [userProjects, setUserProjects] = useState([]);
  const [projectsLoading, setProjectsLoading] = useState(true);

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

  // Fetch user's projects
  useEffect(() => {
    fetchUserProjects();
  }, []);

  const fetchUserProjects = async () => {
    try {
      const response = await axios.get(`${API}/projects`);
      if (response.data.success) {
        setUserProjects(response.data.data.projects);
      }
    } catch (error) {
      console.error('Failed to fetch projects:', error);
    } finally {
      setProjectsLoading(false);
    }
  };

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

      if (response.data.success && response.data.data.project) {
        const project = response.data.data.project;
        
        // Complete all agents with real results from backend
        agents.forEach(agent => {
          clearInterval(progressIntervals[agent.id]);
          const agentResult = project.agents_results[agent.id] || {};
          completeAgent(agent.id, agentResult);
        });

        // Set the real generated project
        setGeneratedProject(project);
        setCurrentStep(agents.length);

        // Refresh projects list
        await fetchUserProjects();

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
      
      if (response.data.success && response.data.data.export_data) {
        const exportData = response.data.data.export_data;
        
        // Create a downloadable JSON file with the export data
        const dataStr = JSON.stringify(exportData, null, 2);
        const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
        
        const exportFileDefaultName = `${exportData.project_info?.name || 'project'}-export.json`;
        
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

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* User Header */}
      <div className="relative overflow-hidden bg-white">
        <div className="absolute inset-0 bg-gradient-to-r from-blue-600/10 to-purple-600/10" />
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <img 
                  src="https://images.unsplash.com/photo-1674027444485-cec3da58eef4?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1Nzl8MHwxfHNlYXJjaHwyfHxhcnRpZmljaWFsJTIwaW50ZWxsaWdlbmNlfGVufDB8fHx8MTc1NjE4OTA2OHww&ixlib=rb-4.1.0&q=85"
                  alt="AI Network"
                  className="w-16 h-16 rounded-2xl object-cover shadow-2xl"
                />
                <div>
                  <h1 className="text-3xl font-bold text-gray-900">
                    Multi-Agent Platform
                  </h1>
                  <p className="text-gray-600">
                    Welcome back, {user?.full_name || user?.username}!
                  </p>
                </div>
              </div>
              <Badge variant="outline" className="text-blue-700 border-blue-200">
                User Dashboard
              </Badge>
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-right">
                <p className="text-sm font-medium text-gray-900">{user?.full_name || user?.username}</p>
                <p className="text-xs text-gray-600">{user?.email}</p>
              </div>
              {user?.profile_picture && (
                <img
                  src={user.profile_picture}
                  alt="Profile"
                  className="h-10 w-10 rounded-full"
                />
              )}
              <Button variant="outline" onClick={logout}>
                <LogOut className="h-4 w-4 mr-2" />
                Logout
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <Tabs defaultValue="generate" className="space-y-6">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="generate">Generate App</TabsTrigger>
            <TabsTrigger value="projects">My Projects</TabsTrigger>
          </TabsList>

          {/* Generate Tab */}
          <TabsContent value="generate">
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
                        <Button variant="outline" size="sm" onClick={() => handleExport(generatedProject.id)}>
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
          </TabsContent>

          {/* Projects Tab */}
          <TabsContent value="projects">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Briefcase className="h-5 w-5 mr-2" />
                  My Projects
                </CardTitle>
                <CardDescription>
                  View and manage your generated projects
                </CardDescription>
              </CardHeader>
              <CardContent>
                {projectsLoading ? (
                  <div className="flex items-center justify-center py-12">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                  </div>
                ) : userProjects.length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {userProjects.map((project) => (
                      <Card key={project.id} className="hover:shadow-md transition-shadow">
                        <CardHeader className="pb-3">
                          <div className="flex items-start justify-between">
                            <div>
                              <CardTitle className="text-lg">{project.name}</CardTitle>
                              <CardDescription className="text-sm line-clamp-2">
                                {project.description}
                              </CardDescription>
                            </div>
                            {project.priority && project.priority !== 'normal' && (
                              <Badge variant="outline" className="capitalize">
                                {project.priority}
                              </Badge>
                            )}
                          </div>
                        </CardHeader>
                        <CardContent className="space-y-3">
                          <div className="text-xs text-gray-500">
                            <div className="flex justify-between mb-1">
                              <span>Created:</span>
                              <span>{formatDate(project.created_at)}</span>
                            </div>
                            <div className="flex justify-between">
                              <span>Technologies:</span>
                              <span>{project.technologies?.length || 0}</span>
                            </div>
                          </div>
                          
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleExport(project.id)}
                            className="w-full"
                          >
                            <Download className="h-3 w-3 mr-2" />
                            Export Project
                          </Button>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-12 text-gray-500">
                    <Briefcase className="h-16 w-16 mx-auto mb-4 opacity-50" />
                    <h3 className="text-lg font-medium mb-2">No Projects Yet</h3>
                    <p className="mb-4">Create your first app to get started</p>
                    <Button onClick={() => document.querySelector('[value="generate"]').click()}>
                      <Play className="h-4 w-4 mr-2" />
                      Generate Your First App
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default UserDashboard;