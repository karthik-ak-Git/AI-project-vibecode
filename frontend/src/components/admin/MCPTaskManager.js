import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Button } from "../ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../ui/card";
import { Input } from "../ui/input";
import { Label } from "../ui/label";
import { Textarea } from "../ui/textarea";
import { Badge } from "../ui/badge";
import { Separator } from "../ui/separator";
import { ScrollArea } from "../ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../ui/select";
import { 
  Plus,
  Zap,
  Linkedin,
  Mail,
  Share2,
  Clock,
  CheckCircle,
  XCircle,
  Pause,
  Play,
  Edit,
  Trash2,
  Eye,
  Calendar,
  Settings
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const MCPTaskManager = () => {
  const [tasks, setTasks] = useState([]);
  const [taskTypes, setTaskTypes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [formData, setFormData] = useState({
    task_type: '',
    name: '',
    description: '',
    parameters: {}
  });
  const [selectedTask, setSelectedTask] = useState(null);

  const fetchTasks = async () => {
    try {
      const response = await axios.get(`${API}/admin/mcp/tasks`);
      if (response.data.success) {
        setTasks(response.data.data.tasks);
      }
    } catch (error) {
      console.error('Failed to fetch MCP tasks:', error);
    }
  };

  const fetchTaskTypes = async () => {
    try {
      const response = await axios.get(`${API}/admin/mcp/task-types`);
      if (response.data.success) {
        setTaskTypes(response.data.data.task_types);
      }
    } catch (error) {
      console.error('Failed to fetch task types:', error);
    }
  };

  useEffect(() => {
    Promise.all([fetchTasks(), fetchTaskTypes()]).finally(() => {
      setLoading(false);
    });
  }, []);

  const handleCreateTask = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post(`${API}/admin/mcp/tasks`, formData);
      if (response.data.success) {
        await fetchTasks();
        setShowCreateForm(false);
        resetForm();
      }
    } catch (error) {
      console.error('Failed to create MCP task:', error);
    }
  };

  const handleUpdateTaskStatus = async (taskId, newStatus) => {
    try {
      const response = await axios.put(`${API}/admin/mcp/tasks/${taskId}`, {
        status: newStatus
      });
      if (response.data.success) {
        await fetchTasks();
      }
    } catch (error) {
      console.error('Failed to update task status:', error);
    }
  };

  const handleDeleteTask = async (taskId) => {
    if (window.confirm('Are you sure you want to delete this task?')) {
      try {
        const response = await axios.delete(`${API}/admin/mcp/tasks/${taskId}`);
        if (response.data.success) {
          await fetchTasks();
        }
      } catch (error) {
        console.error('Failed to delete task:', error);
      }
    }
  };

  const resetForm = () => {
    setFormData({
      task_type: '',
      name: '',
      description: '',
      parameters: {}
    });
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'active':
        return <Play className="h-4 w-4 text-green-600" />;
      case 'paused':
        return <Pause className="h-4 w-4 text-yellow-600" />;
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-blue-600" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-600" />;
      default:
        return <Clock className="h-4 w-4 text-gray-600" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800';
      case 'paused':
        return 'bg-yellow-100 text-yellow-800';
      case 'completed':
        return 'bg-blue-100 text-blue-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getTaskTypeIcon = (taskType) => {
    switch (taskType) {
      case 'linkedin_post':
        return <Linkedin className="h-5 w-5 text-blue-600" />;
      case 'email_campaign':
        return <Mail className="h-5 w-5 text-green-600" />;
      case 'social_media_post':
        return <Share2 className="h-5 w-5 text-purple-600" />;
      default:
        return <Zap className="h-5 w-5 text-gray-600" />;
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">MCP Task Manager</h2>
          <p className="text-gray-600">Create and manage automation tasks</p>
        </div>
        <Button
          onClick={() => setShowCreateForm(true)}
          className="bg-blue-600 hover:bg-blue-700"
        >
          <Plus className="h-4 w-4 mr-2" />
          Create Task
        </Button>
      </div>

      {/* Create Task Form */}
      {showCreateForm && (
        <Card>
          <CardHeader>
            <CardTitle>Create New MCP Task</CardTitle>
            <CardDescription>Set up a new automation task</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreateTask} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="task_type">Task Type</Label>
                  <Select
                    value={formData.task_type}
                    onValueChange={(value) => setFormData({...formData, task_type: value})}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select task type" />
                    </SelectTrigger>
                    <SelectContent>
                      {taskTypes.map((type) => (
                        <SelectItem key={type.id} value={type.id}>
                          <div className="flex items-center space-x-2">
                            {getTaskTypeIcon(type.id)}
                            <span>{type.name}</span>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="name">Task Name</Label>
                  <Input
                    id="name"
                    value={formData.name}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                    placeholder="Enter task name"
                    required
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) => setFormData({...formData, description: e.target.value})}
                  placeholder="Describe what this task will do"
                  rows={3}
                />
              </div>

              {/* Task-specific parameters based on type */}
              {formData.task_type === 'linkedin_post' && (
                <div className="space-y-4 p-4 bg-blue-50 rounded-lg">
                  <h4 className="font-medium text-blue-900">LinkedIn Post Parameters</h4>
                  <div className="space-y-2">
                    <Label htmlFor="content">Post Content</Label>
                    <Textarea
                      id="content"
                      placeholder="Enter your LinkedIn post content..."
                      onChange={(e) => setFormData({
                        ...formData,
                        parameters: {...formData.parameters, content: e.target.value}
                      })}
                      rows={4}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="hashtags">Hashtags (comma-separated)</Label>
                    <Input
                      id="hashtags"
                      placeholder="#automation, #ai, #productivity"
                      onChange={(e) => setFormData({
                        ...formData,
                        parameters: {...formData.parameters, hashtags: e.target.value.split(',')}
                      })}
                    />
                  </div>
                </div>
              )}

              <div className="flex justify-end space-x-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setShowCreateForm(false);
                    resetForm();
                  }}
                >
                  Cancel
                </Button>
                <Button type="submit" className="bg-blue-600 hover:bg-blue-700">
                  Create Task
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Tasks List */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        {tasks.map((task) => (
          <Card key={task.id} className="hover:shadow-md transition-shadow">
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between">
                <div className="flex items-center space-x-3">
                  {getTaskTypeIcon(task.task_type)}
                  <div>
                    <CardTitle className="text-lg">{task.name}</CardTitle>
                    <CardDescription className="text-sm">
                      {task.task_type.replace('_', ' ').toUpperCase()}
                    </CardDescription>
                  </div>
                </div>
                <Badge className={getStatusColor(task.status)}>
                  <div className="flex items-center space-x-1">
                    {getStatusIcon(task.status)}
                    <span className="capitalize">{task.status}</span>
                  </div>
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              <p className="text-sm text-gray-600 line-clamp-2">
                {task.description}
              </p>
              
              <div className="text-xs text-gray-500 space-y-1">
                <div className="flex justify-between">
                  <span>Created:</span>
                  <span>{formatDate(task.created_at)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Executions:</span>
                  <span>{task.execution_count || 0}</span>
                </div>
                {task.last_executed && (
                  <div className="flex justify-between">
                    <span>Last run:</span>
                    <span>{formatDate(task.last_executed)}</span>
                  </div>
                )}
              </div>

              <Separator />

              <div className="flex justify-between items-center">
                <div className="flex space-x-1">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setSelectedTask(task)}
                  >
                    <Eye className="h-3 w-3" />
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                  >
                    <Edit className="h-3 w-3" />
                  </Button>
                </div>
                
                <div className="flex space-x-1">
                  {task.status === 'active' ? (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleUpdateTaskStatus(task.id, 'paused')}
                    >
                      <Pause className="h-3 w-3" />
                    </Button>
                  ) : (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleUpdateTaskStatus(task.id, 'active')}
                    >
                      <Play className="h-3 w-3" />
                    </Button>
                  )}
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleDeleteTask(task.id)}
                    className="text-red-600 hover:text-red-700"
                  >
                    <Trash2 className="h-3 w-3" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {tasks.length === 0 && (
        <Card>
          <CardContent className="text-center py-12">
            <Zap className="h-16 w-16 mx-auto mb-4 text-gray-400" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No MCP Tasks</h3>
            <p className="text-gray-600 mb-4">
              Create your first automation task to get started
            </p>
            <Button
              onClick={() => setShowCreateForm(true)}
              className="bg-blue-600 hover:bg-blue-700"
            >
              <Plus className="h-4 w-4 mr-2" />
              Create Your First Task
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default MCPTaskManager;