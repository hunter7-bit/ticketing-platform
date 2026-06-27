import { useState, useEffect } from 'react';
import { Ticket, Calendar, MapPin, User, X, CheckCircle2, AlertCircle } from 'lucide-react';

// ============================================================================
// PRODUCTION ARCHITECTURE NOTE:
// In a real codebase, everything below would be split into multiple files:
// - src/components/Navbar.jsx
// - src/components/EventCard.jsx
// - src/components/CheckoutModal.jsx
// - src/pages/Home.jsx
// ============================================================================

export default function App() {
  // --- STATE MANAGEMENT ---
  const [token, setToken] = useState(null);
  const [events, setEvents] = useState([]);
  const [loadingEvents, setLoadingEvents] = useState(true);
  
  // Modal & Checkout State
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [authError, setAuthError] = useState(null);
  
  // Reservation Flow
  const [isReserving, setIsReserving] = useState(false);
  const [reservation, setReservation] = useState(null);
  const [checkoutStatus, setCheckoutStatus] = useState('idle'); // idle, processing, success, error
  const [checkoutMessage, setCheckoutMessage] = useState(null);

  // --- 1. INITIAL DATA FETCH FUNCTION ---
  const fetchEvents = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/events/');
      const data = await response.json();
      setEvents(data);
      
      // NEW FIX: If the modal is currently open, update its data with the fresh fetch!
      setSelectedEvent(currentSelected => {
        if (!currentSelected) return null;
        // Find the fresh version of this exact event from the new data
        return data.find(e => e.id === currentSelected.id) || currentSelected;
      });
      
    } catch (error) {
      console.error("Failed to load events:", error);
    } finally {
      setLoadingEvents(false);
    }
  };

  // Run once on load
  useEffect(() => {
    fetchEvents();
  }, []);

  // --- 2. WEBSOCKET LISTENER ---
  // Connect to the backend and listen for broadcast commands
  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/api/v1/ws');

    ws.onopen = () => console.log("Connected to live ticket updates!");
    
    ws.onmessage = (event) => {
      if (event.data === "refresh_events") {
        console.log("Activity detected! Refreshing ticket counts...");
        // Re-fetch the events from the server to get the latest accurate numbers!
        fetchEvents();
      }
    };

    // Cleanup connection if the user closes the page
    return () => ws.close();
  }, []);

  // --- AUTHENTICATION ---
  const handleLogin = async (e) => {
    e.preventDefault();
    setAuthError(null);
    const formData = new URLSearchParams();
    formData.append('username', e.target.email.value);
    formData.append('password', e.target.password.value);

    try {
      const response = await fetch('http://localhost:8000/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData.toString(),
      });
      const data = await response.json();
      
      if (response.ok) {
        setToken(data.access_token);
        setShowAuthModal(false);
      } else {
        setAuthError(data.detail || 'Login failed');
      }
    } catch (error) {
      setAuthError('Could not connect to server.');
    }
  };

  // --- TICKET RESERVATION (skip_locked) ---
  const handleReserve = async (tierId) => {
    if (!token) {
      setShowAuthModal(true);
      return;
    }

    setIsReserving(true);
    setCheckoutMessage(null);
    setCheckoutStatus('idle');

    try {
      const response = await fetch('http://localhost:8000/api/v1/tickets/reserve', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}` 
        },
        body: JSON.stringify({ tier_id: tierId }),
      });
      const data = await response.json();

      if (response.ok) {
        setReservation(data);
      } else {
        setCheckoutStatus('error');
        setCheckoutMessage(data.detail);
      }
    } catch (error) {
      setCheckoutStatus('error');
      setCheckoutMessage('Network error occurred.');
    } finally {
      setIsReserving(false);
    }
  };

  // --- COMPLETE CHECKOUT ---
  const handleCheckout = async () => {
    setCheckoutStatus('processing');
    try {
      const response = await fetch('http://localhost:8000/api/v1/tickets/checkout', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}` 
        },
        body: JSON.stringify({ ticket_id: reservation.ticket_id }),
      });
      const data = await response.json();

      if (response.ok) {
        setCheckoutStatus('success');
        // Refresh event data in the background to update remaining tickets
        fetch('http://localhost:8000/api/v1/events/')
          .then(res => res.json())
          .then(data => setEvents(data));
      } else {
        setCheckoutStatus('error');
        setCheckoutMessage(data.detail || 'Checkout failed. Time expired.');
        setReservation(null);
      }
    } catch (error) {
      setCheckoutStatus('error');
      setCheckoutMessage('Network error during payment.');
    }
  };

  // --- HELPERS ---
  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', { 
      weekday: 'short', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' 
    });
  };

  // --- RENDER ---
  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 font-sans selection:bg-rose-500/30">
      
      {/* NAVBAR */}
      <nav className="sticky top-0 z-40 bg-slate-950/80 backdrop-blur-md border-b border-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2 text-rose-500">
            <Ticket size={28} />
            <span className="text-xl font-bold tracking-tight text-white">Tix<span className="text-rose-500">Master</span></span>
          </div>
          <div>
            {token ? (
              <button onClick={() => setToken(null)} className="text-sm font-medium hover:text-rose-400 transition-colors">Log Out</button>
            ) : (
              <button onClick={() => setShowAuthModal(true)} className="flex items-center gap-2 bg-slate-800 hover:bg-slate-700 text-white px-4 py-2 rounded-full text-sm font-medium transition-colors">
                <User size={16} /> Sign In
              </button>
            )}
          </div>
        </div>
      </nav>

      {/* HERO SECTION */}
      <div className="relative overflow-hidden bg-slate-900 border-b border-slate-800">
        <div className="absolute inset-0 bg-gradient-to-r from-rose-900/20 to-slate-900/10 mix-blend-multiply" />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 lg:py-24 relative z-10">
          <h1 className="text-4xl lg:text-6xl font-extrabold tracking-tight mb-4 text-white">
            Unforgettable <br/><span className="text-transparent bg-clip-text bg-gradient-to-r from-rose-400 to-orange-400">Live Experiences.</span>
          </h1>
          <p className="text-lg text-slate-400 max-w-xl">
            Secure your spot at the biggest events. Powered by high-concurrency row-level locks so you never lose your ticket mid-checkout.
          </p>
        </div>
      </div>

      {/* EVENT GRID */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <h2 className="text-2xl font-bold mb-8 text-white">Trending Events</h2>
        
        {loadingEvents ? (
          <div className="flex justify-center py-20">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-rose-500"></div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {events.map((event) => (
              <div key={event.id} className="bg-slate-900 rounded-2xl overflow-hidden border border-slate-800 hover:border-slate-700 hover:shadow-xl hover:shadow-rose-500/5 transition-all group cursor-pointer" onClick={() => setSelectedEvent(event)}>
                {/* Image Placeholder with Gradient */}
                <div className="h-48 bg-gradient-to-br from-indigo-900/80 to-slate-900 relative">
                  <div className="absolute bottom-4 left-4 bg-slate-950/80 backdrop-blur px-3 py-1 rounded-md text-xs font-bold text-rose-400 uppercase tracking-wider">
                    Concert
                  </div>
                </div>
                <div className="p-6">
                  <h3 className="text-xl font-bold text-white mb-2 group-hover:text-rose-400 transition-colors line-clamp-1">{event.title}</h3>
                  <div className="flex items-center text-sm text-slate-400 mb-2 gap-2">
                    <Calendar size={16} /> {formatDate(event.start_time)}
                  </div>
                  <div className="flex items-center text-sm text-slate-400 mb-6 gap-2 line-clamp-1">
                    <MapPin size={16} className="flex-shrink-0" /> {event.venue}
                  </div>
                  <button className="w-full bg-slate-800 hover:bg-slate-700 text-white font-medium py-2.5 rounded-lg transition-colors border border-slate-700">
                    View Tickets
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>

      {/* TICKET SELECTION / CHECKOUT MODAL */}
      {selectedEvent && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-slate-950/80 backdrop-blur-sm" onClick={() => {if(checkoutStatus !== 'processing') setSelectedEvent(null); setReservation(null); setCheckoutStatus('idle')}}></div>
          <div className="relative bg-slate-900 rounded-2xl shadow-2xl border border-slate-800 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            
            {/* Modal Header */}
            <div className="flex justify-between items-center p-6 border-b border-slate-800 sticky top-0 bg-slate-900/90 backdrop-blur">
              <h3 className="text-xl font-bold text-white pr-8 line-clamp-1">{selectedEvent.title}</h3>
              <button onClick={() => {setSelectedEvent(null); setReservation(null); setCheckoutStatus('idle')}} className="text-slate-400 hover:text-white bg-slate-800 rounded-full p-1">
                <X size={20} />
              </button>
            </div>

            <div className="p-6">
              {/* STEP 1: CHOOSE A TIER */}
              {/* THE FIX: We now allow Step 1 to render if the status is 'error' so you can see the message! */}
              {!reservation && (checkoutStatus === 'idle' || checkoutStatus === 'error') && (
                <div className="space-y-4">
                  <p className="text-sm text-slate-400 mb-4">Select your preferred ticket type below.</p>
                  
                  {selectedEvent.tiers.map(tier => (
                    <div key={tier.id} className="flex flex-col sm:flex-row sm:items-center justify-between p-4 rounded-xl border border-slate-700 bg-slate-800/50 hover:bg-slate-800 transition-colors gap-4">
                      <div>
                        <h4 className="text-lg font-bold text-white">{tier.name}</h4>
                        <p className="text-sm text-slate-400 font-medium">₹{tier.price}</p>
                        
                        {/* Dynamic capacity badge */}
                        {tier.remaining_capacity === 0 ? (
                          <span className="inline-block mt-2 text-xs font-bold bg-slate-700 text-slate-400 px-2 py-1 rounded">SOLD OUT</span>
                        ) : tier.remaining_capacity < 10 ? (
                          <span className="inline-block mt-2 text-xs font-bold bg-orange-900/50 text-orange-400 border border-orange-800/50 px-2 py-1 rounded animate-pulse">ONLY {tier.remaining_capacity} LEFT</span>
                        ) : (
                          <span className="inline-block mt-2 text-xs font-medium text-green-400">Available</span>
                        )}
                      </div>
                      
                      <button 
                        onClick={() => handleReserve(tier.id)}
                        disabled={isReserving || tier.remaining_capacity === 0}
                        className="bg-rose-600 hover:bg-rose-500 disabled:bg-slate-700 disabled:text-slate-500 text-white font-bold py-2 px-6 rounded-lg transition-colors whitespace-nowrap"
                      >
                        {isReserving ? 'Locking...' : 'Add to Cart'}
                      </button>
                    </div>
                  ))}
                  
                  {/* The error message that was hiding from us! */}
                  {checkoutStatus === 'error' && (
                    <div className="mt-4 p-3 bg-red-900/30 border border-red-800 rounded-lg flex gap-2 text-red-400 text-sm">
                      <AlertCircle size={18} /> {checkoutMessage}
                    </div>
                  )}
                </div>
              )}

              {/* STEP 2: CHECKOUT (TICKET LOCKED) */}
              {reservation && checkoutStatus !== 'success' && (
                <div className="space-y-6">
                  <div className="bg-emerald-900/20 border border-emerald-800/50 rounded-xl p-6 text-center relative overflow-hidden">
                    <div className="absolute top-0 left-0 w-full h-1 bg-emerald-500 animate-[pulse_1s_ease-in-out_infinite]" />
                    <CheckCircle2 size={48} className="text-emerald-400 mx-auto mb-3" />
                    <h3 className="text-2xl font-bold text-emerald-400 mb-1">Ticket Secured!</h3>
                    <p className="text-sm text-emerald-200/70 mb-4">{reservation.message}</p>
                    <div className="bg-slate-950 rounded-lg p-3 font-mono text-xs text-slate-400 break-all border border-slate-800">
                      ID: {reservation.ticket_id}
                    </div>
                  </div>

                  <button 
                    onClick={handleCheckout}
                    disabled={checkoutStatus === 'processing'}
                    className="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-4 rounded-xl transition-all shadow-lg shadow-blue-900/20 disabled:opacity-50 text-lg flex justify-center items-center gap-2"
                  >
                    {checkoutStatus === 'processing' ? 'Processing Payment...' : 'Pay Now & Complete Booking'}
                  </button>

                  {checkoutStatus === 'error' && (
                    <div className="p-4 bg-red-900/30 border border-red-800 rounded-lg flex gap-2 text-red-400 text-sm">
                      <AlertCircle size={18} /> {checkoutMessage}
                    </div>
                  )}
                </div>
              )}

              {/* STEP 3: SUCCESS */}
              {checkoutStatus === 'success' && (
                <div className="py-8 text-center space-y-4">
                  <div className="mx-auto w-20 h-20 bg-rose-500 rounded-full flex items-center justify-center shadow-lg shadow-rose-500/30 mb-6">
                    <Ticket size={40} className="text-white" />
                  </div>
                  <h3 className="text-3xl font-extrabold text-white">You're going!</h3>
                  <p className="text-slate-400 max-w-sm mx-auto">Your ticket has been booked successfully. The QR code will be emailed to you shortly.</p>
                  <button 
                    onClick={() => {setSelectedEvent(null); setReservation(null); setCheckoutStatus('idle');}}
                    className="mt-8 bg-slate-800 hover:bg-slate-700 text-white font-medium py-2.5 px-6 rounded-full transition-colors border border-slate-700"
                  >
                    Browse More Events
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* LOGIN MODAL */}
      {showAuthModal && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-slate-950/90 backdrop-blur-sm" onClick={() => setShowAuthModal(false)}></div>
          <div className="relative bg-slate-900 rounded-2xl p-8 border border-slate-800 w-full max-w-sm shadow-2xl">
            <h3 className="text-2xl font-bold text-white mb-6 text-center">Welcome Back</h3>
            
            {authError && (
              <div className="mb-4 p-3 bg-red-900/30 border border-red-800 rounded-lg text-red-400 text-sm text-center">
                {authError}
              </div>
            )}

            <form onSubmit={handleLogin} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-400 mb-1">Email</label>
                <input name="email" type="email" defaultValue="test@example.com" className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-rose-500 transition-colors" required />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-400 mb-1">Password</label>
                <input name="password" type="password" defaultValue="secret123" className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-rose-500 transition-colors" required />
              </div>
              <button type="submit" className="w-full bg-rose-600 hover:bg-rose-500 text-white font-bold py-3 rounded-lg transition-colors mt-2">
                Sign In
              </button>
            </form>
          </div>
        </div>
      )}

    </div>
  );
}