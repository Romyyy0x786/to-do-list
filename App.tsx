import { useState, useEffect } from 'react'
import axios from 'axios'

interface Board { _id: string; title: string; owner_id: string; }
interface Todo { _id: string; content: string; status: string; board_id: string; }

const API_URL = 'http://localhost:8000'

function App() {
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'))
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [boards, setBoards] = useState<Board[]>([])
  const [newBoardTitle, setNewBoardTitle] = useState('')
  const [activeBoard, setActiveBoard] = useState<Board | null>(null)
  const [todos, setTodos] = useState<Todo[]>([])
  const [newTodo, setNewTodo] = useState('')

  const authHeader = { headers: { Authorization: `Bearer ${token}` } }

  // --- AUTH FUNCTIONS ---
  const login = async () => {
    try {
      const formData = new FormData()
      formData.append('username', email)
      formData.append('password', password)
      const res = await axios.post(`${API_URL}/token`, formData)
      localStorage.setItem('token', res.data.access_token)
      setToken(res.data.access_token)
    } catch (e) { alert('Login failed') }
  }

  const register = async () => {
    try {
      await axios.post(`${API_URL}/register`, { email, password })
      alert('Registered! Now Login.')
    } catch (e) { alert('Registration failed') }
  }

  const logout = () => {
    localStorage.removeItem('token')
    setToken(null)
    setBoards([])
    setActiveBoard(null)
  }

  // --- BOARD FUNCTIONS ---
  const fetchBoards = async () => {
    try {
      const res = await axios.get(`${API_URL}/boards`, authHeader)
      setBoards(res.data)
    } catch (e) { console.error(e) }
  }

  const createBoard = async () => {
    if (!newBoardTitle) return
    try {
      await axios.post(`${API_URL}/boards`, { title: newBoardTitle }, authHeader)
      setNewBoardTitle('')
      fetchBoards()
    } catch (e) { console.error(e) }
  }

  const deleteBoard = async (id: string) => {
    try {
        await axios.delete(`${API_URL}/boards/${id}`, authHeader)
        if (activeBoard && activeBoard._id === id) setActiveBoard(null);
        fetchBoards();
    } catch (e) { console.error(e) }
  }

  // --- TODO FUNCTIONS ---
  const fetchTodos = async (boardId: string) => {
    try {
      const res = await axios.get(`${API_URL}/boards/${boardId}/todos`, authHeader)
      setTodos(res.data)
    } catch (e) { console.error(e) }
  }

  const createTodo = async () => {
    if (!newTodo || !activeBoard) return
    try {
      await axios.post(`${API_URL}/boards/${activeBoard._id}/todos`, { content: newTodo, status: "pending" }, authHeader)
      setNewTodo('')
      fetchTodos(activeBoard._id)
    } catch (e) { console.error(e) }
  }

  const deleteTodo = async (id: string) => {
      try {
          await axios.delete(`${API_URL}/todos/${id}`, authHeader)
          if(activeBoard) fetchTodos(activeBoard._id)
      } catch (e) { console.error(e) }
  }

  const updateTodoStatus = async (id: string, currentStatus: string) => {
      const newStatus = currentStatus === "pending" ? "done" : "pending";
      try {
          await axios.put(`${API_URL}/todos/${id}`, { status: newStatus }, authHeader)
          if(activeBoard) fetchTodos(activeBoard._id)
      } catch (e) { console.error(e) }
  }

  // --- EFFECTS ---
  useEffect(() => { if (token) fetchBoards() }, [token])
  useEffect(() => { if (activeBoard) fetchTodos(activeBoard._id) }, [activeBoard])

  // --- RENDER UI ---
  if (!token) return (
    <div className="flex h-screen items-center justify-center bg-gray-100">
      <div className="p-8 bg-white shadow-lg rounded-lg w-96">
        <h1 className="text-2xl font-bold mb-4 text-center">Todo App Login</h1>
        <input className="w-full p-2 mb-2 border rounded" placeholder="Email" onChange={(e) => setEmail(e.target.value)} />
        <input className="w-full p-2 mb-4 border rounded" type="password" placeholder="Password" onChange={(e) => setPassword(e.target.value)} />
        <div className="flex gap-2">
            <button className="flex-1 bg-blue-500 text-white p-2 rounded hover:bg-blue-600" onClick={login}>Login</button>
            <button className="flex-1 bg-green-500 text-white p-2 rounded hover:bg-green-600" onClick={register}>Register</button>
        </div>
      </div>
    </div>
  )

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <div className="w-1/4 bg-white border-r p-4 overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-bold">My Boards</h2>
            <button onClick={logout} className="text-xs text-red-500 underline">Logout</button>
        </div>
        <div className="mb-4 flex gap-2">
          <input className="border p-2 rounded w-full" placeholder="New Board" value={newBoardTitle} onChange={(e) => setNewBoardTitle(e.target.value)} />
          <button className="bg-blue-500 text-white px-4 rounded" onClick={createBoard}>+</button>
        </div>
        <div className="space-y-2">
          {boards.map(board => (
            <div key={board._id} 
                className={`p-3 rounded cursor-pointer flex justify-between group ${activeBoard?._id === board._id ? 'bg-blue-100 border-blue-300 border' : 'bg-gray-100 hover:bg-gray-200'}`}
                onClick={() => setActiveBoard(board)}>
              <span>{board.title}</span>
              <button className="text-red-400 hidden group-hover:block" onClick={(e) => { e.stopPropagation(); deleteBoard(board._id); }}>×</button>
            </div>
          ))}
        </div>
      </div>

      {/* Main Content */}
      <div className="w-3/4 p-8">
        {activeBoard ? (
          <>
            <h1 className="text-3xl font-bold mb-6">{activeBoard.title}</h1>
            <div className="flex gap-2 mb-6">
              <input className="border p-3 rounded w-full shadow-sm" placeholder="Add a new task..." value={newTodo} onChange={(e) => setNewTodo(e.target.value)} />
              <button className="bg-green-600 text-white px-6 rounded font-semibold" onClick={createTodo}>Add Task</button>
            </div>
            <div className="space-y-3">
              {todos.map(todo => (
                <div key={todo._id} className="flex items-center bg-white p-4 rounded shadow-sm border border-gray-100">
                  <input type="checkbox" className="mr-4 h-5 w-5" checked={todo.status === 'done'} onChange={() => updateTodoStatus(todo._id, todo.status)} />
                  <span className={`flex-1 text-lg ${todo.status === 'done' ? 'line-through text-gray-400' : ''}`}>{todo.content}</span>
                  <button className="text-red-500 hover:text-red-700" onClick={() => deleteTodo(todo._id)}>Delete</button>
                </div>
              ))}
              {todos.length === 0 && <p className="text-gray-400 text-center italic mt-10">No tasks yet.</p>}
            </div>
          </>
        ) : <div className="flex items-center justify-center h-full text-gray-400">Select a board to view tasks</div>}
      </div>
    </div>
  )
}
export default App