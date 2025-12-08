import React from "react";

export default function AdminLayout({ children }) {
  return (
    <div className="min-h-screen bg-gray-100">
      <nav className="bg-blue-600 text-white p-4 font-bold">AI Agent Admin</nav>
      <main className="p-8">{children}</main>
    </div>
  );
}

