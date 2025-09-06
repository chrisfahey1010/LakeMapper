import { Link, Outlet } from 'react-router-dom'

export default function App() {
  return (
    <div className="app">
      <header className="app__header">
        <Link to="/" className="app__brand">LakeMapper</Link>
      </header>
      <main className="app__main">
        <Outlet />
      </main>
      <footer className="app__footer">
        Data © Minnesota DNR. For planning, not navigation.
      </footer>
    </div>
  )
}


