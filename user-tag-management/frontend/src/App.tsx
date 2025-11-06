import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Users from './pages/Users.tsx'
import Tags from './pages/Tags.tsx'
import Layout from './components/Layout.tsx'

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Users />} />
          <Route path="/users" element={<Users />} />
          <Route path="/tags" element={<Tags />} />
        </Routes>
      </Layout>
    </Router>
  )
}

export default App
