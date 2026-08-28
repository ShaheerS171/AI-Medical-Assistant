/**
 * Supabase Authentication Client Logic
 * Provides full Sign In, Sign Up, Password Reset, and Sign Out capabilities.
 */

// ============================================================================
// UI VIEW CONTROLLER (Defined first so UI works unconditionally)
// ============================================================================
function showView(viewId) {
  console.log("Switching view to:", viewId);
  hideAlert();
  
  const views = ['signInView', 'signUpView', 'forgotPasswordView', 'dashboardView'];
  views.forEach(id => {
    const el = document.getElementById(id);
    if (el) {
      if (id === viewId) {
        el.classList.remove('hidden');
        el.classList.add('active');
        el.style.display = 'block';
      } else {
        el.classList.add('hidden');
        el.classList.remove('active');
        el.style.display = 'none';
      }
    }
  });

  // Update Top Navigation Tabs
  const tabSignIn = document.getElementById('tabSignIn');
  const tabSignUp = document.getElementById('tabSignUp');
  const authTabs = document.getElementById('authTabs');

  if (viewId === 'dashboardView') {
    if (authTabs) authTabs.style.display = 'none';
  } else {
    if (authTabs) authTabs.style.display = 'flex';
    if (viewId === 'signInView') {
      tabSignIn?.classList.add('active');
      tabSignUp?.classList.remove('active');
    } else if (viewId === 'signUpView') {
      tabSignUp?.classList.add('active');
      tabSignIn?.classList.remove('active');
    } else {
      tabSignIn?.classList.remove('active');
      tabSignUp?.classList.remove('active');
    }
  }
}

function togglePasswordVisibility(inputId, btn) {
  const input = document.getElementById(inputId);
  const icon = btn.querySelector('i');
  if (input.type === 'password') {
    input.type = 'text';
    icon.className = 'fa-regular fa-eye-slash';
  } else {
    input.type = 'password';
    icon.className = 'fa-regular fa-eye';
  }
}

function showAlert(message, type = 'error') {
  const banner = document.getElementById('alertBanner');
  const msgEl = document.getElementById('alertMessage');
  const iconEl = document.getElementById('alertIcon');

  if (msgEl) msgEl.textContent = message;
  if (banner) {
    banner.className = `alert-banner ${type}`;
    if (iconEl) iconEl.className = type === 'success' ? 'fa-solid fa-circle-check' : 'fa-solid fa-circle-exclamation';
    banner.classList.remove('hidden');
    banner.style.display = 'flex';
  }
}

function hideAlert() {
  const banner = document.getElementById('alertBanner');
  if (banner) {
    banner.classList.add('hidden');
    banner.style.display = 'none';
  }
}

function setButtonLoading(btnId, isLoading) {
  const btn = document.getElementById(btnId);
  if (!btn) return;
  const textEl = btn.querySelector('.btn-text');
  const spinnerEl = btn.querySelector('.btn-spinner');
  
  if (isLoading) {
    btn.disabled = true;
    textEl?.classList.add('hidden');
    spinnerEl?.classList.remove('hidden');
  } else {
    btn.disabled = false;
    textEl?.classList.remove('hidden');
    spinnerEl?.classList.add('hidden');
  }
}

// ============================================================================
// CONFIGURATION & CLIENT INITIALIZATION
// ============================================================================
const SUPABASE_URL = "https://pmrubksxiavmzbxbbfwa.supabase.co"; 
const SUPABASE_ANON_KEY = "sb_publishable_tAV_fEqKEgL2tyd1UoyTdg_J8SKGW4x";

let supabase = null;

try {
  if (window.supabase && typeof window.supabase.createClient === 'function' && SUPABASE_URL) {
    supabase = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
    console.log("Supabase client initialized successfully.");
  }
} catch (err) {
  console.error("Error creating Supabase client:", err);
}

// ============================================================================
// AUTHENTICATION ACTIONS (Sign In, Sign Up, Sign Out, OAuth)
// ============================================================================

/**
 * Sign In User with Email & Password
 */
async function handleSignIn(event) {
  event.preventDefault();
  hideAlert();

  const email = document.getElementById('signinEmail').value.trim();
  const password = document.getElementById('signinPassword').value;

  if (!supabase) {
    showAlert("Supabase client is not ready. Please verify your SUPABASE_ANON_KEY in auth.js.");
    return;
  }

  setButtonLoading('btnSignIn', true);

  try {
    const { data, error } = await supabase.auth.signInWithPassword({
      email: email,
      password: password,
    });

    if (error) throw error;

    showAlert("Successfully signed in!", "success");
    renderDashboard(data.user, data.session);
    showView('dashboardView');
  } catch (err) {
    console.error("Sign in error:", err);
    showAlert(err.message || "Failed to sign in. Please check your email/password.");
  } finally {
    setButtonLoading('btnSignIn', false);
  }
}

/**
 * Sign Up New User
 */
async function handleSignUp(event) {
  event.preventDefault();
  hideAlert();

  const fullName = document.getElementById('signupName').value.trim();
  const email = document.getElementById('signupEmail').value.trim();
  const password = document.getElementById('signupPassword').value;

  if (!supabase) {
    showAlert("Supabase client is not ready. Please check your SUPABASE_ANON_KEY.");
    return;
  }

  setButtonLoading('btnSignUp', true);

  try {
    const { data, error } = await supabase.auth.signUp({
      email: email,
      password: password,
      options: {
        data: {
          full_name: fullName,
        }
      }
    });

    if (error) throw error;

    if (data.user && !data.session) {
      showAlert("Registration successful! Check your email to confirm your account.", "success");
      showView('signInView');
    } else if (data.session) {
      showAlert("Account created & logged in successfully!", "success");
      renderDashboard(data.user, data.session);
      showView('dashboardView');
    }
  } catch (err) {
    console.error("Sign up error:", err);
    showAlert(err.message || "Failed to create account.");
  } finally {
    setButtonLoading('btnSignUp', false);
  }
}

/**
 * Reset Password Link Email
 */
async function handleResetPassword(event) {
  event.preventDefault();
  hideAlert();

  const email = document.getElementById('resetEmail').value.trim();

  if (!supabase) {
    showAlert("Supabase client is not initialized.");
    return;
  }

  setButtonLoading('btnReset', true);

  try {
    const { error } = await supabase.auth.resetPasswordForEmail(email, {
      redirectTo: window.location.origin,
    });

    if (error) throw error;

    showAlert("Password reset link sent to your email!", "success");
  } catch (err) {
    console.error("Reset password error:", err);
    showAlert(err.message || "Failed to send reset link.");
  } finally {
    setButtonLoading('btnReset', false);
  }
}

/**
 * Sign Out User
 */
async function handleSignOut() {
  hideAlert();
  if (!supabase) return;

  setButtonLoading('btnSignOut', true);

  try {
    const { error } = await supabase.auth.signOut();
    if (error) throw error;

    showAlert("Signed out successfully.", "success");
    showView('signInView');
  } catch (err) {
    console.error("Sign out error:", err);
    showAlert(err.message || "Error signing out.");
  } finally {
    setButtonLoading('btnSignOut', false);
  }
}

/**
 * Social OAuth Login (Google / GitHub)
 */
async function handleOAuthLogin(provider) {
  if (!supabase) {
    showAlert("Supabase client is not initialized.");
    return;
  }

  try {
    const { error } = await supabase.auth.signInWithOAuth({
      provider: provider,
      options: {
        redirectTo: window.location.href,
      }
    });

    if (error) throw error;
  } catch (err) {
    console.error(`OAuth login error (${provider}):`, err);
    showAlert(err.message || `Failed to sign in with ${provider}. Ensure ${provider} provider is enabled in your Supabase dashboard.`);
  }
}

// ============================================================================
// SESSION MANAGEMENT & USER RENDER
// ============================================================================

function renderDashboard(user, session) {
  if (!user) return;

  const name = user.user_metadata?.full_name || user.email.split('@')[0];
  const avatarLetter = name.charAt(0).toUpperCase();

  const userAvatar = document.getElementById('userAvatar');
  const userNameDisplay = document.getElementById('userNameDisplay');
  const userEmailDisplay = document.getElementById('userEmailDisplay');
  const userIdDisplay = document.getElementById('userIdDisplay');
  const lastSignInDisplay = document.getElementById('lastSignInDisplay');

  if (userAvatar) userAvatar.textContent = avatarLetter;
  if (userNameDisplay) userNameDisplay.textContent = name;
  if (userEmailDisplay) userEmailDisplay.textContent = user.email;
  if (userIdDisplay) userIdDisplay.textContent = user.id;

  const lastSignIn = user.last_sign_in_at 
    ? new Date(user.last_sign_in_at).toLocaleString() 
    : 'Just now';
  if (lastSignInDisplay) lastSignInDisplay.textContent = lastSignIn;

  window.currentUserSession = session;
}

function copyAccessToken() {
  if (window.currentUserSession?.access_token) {
    navigator.clipboard.writeText(window.currentUserSession.access_token);
    showAlert("Access Token (JWT) copied to clipboard!", "success");
  } else {
    showAlert("No active session token found.");
  }
}

// Check initial session on page load
document.addEventListener('DOMContentLoaded', async () => {
  if (!supabase) return;

  try {
    const { data: { session } } = await supabase.auth.getSession();
    if (session) {
      renderDashboard(session.user, session);
      showView('dashboardView');
    }

    supabase.auth.onAuthStateChange((event, session) => {
      console.log("Auth Event:", event);
      if (event === 'SIGNED_IN' && session) {
        renderDashboard(session.user, session);
        showView('dashboardView');
      } else if (event === 'SIGNED_OUT') {
        showView('signInView');
      }
    });
  } catch (e) {
    console.error("Auth session check error:", e);
  }
});
