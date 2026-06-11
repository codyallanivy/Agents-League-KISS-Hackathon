# Product Vision — Pizza Shop Ordering App

**Vision:** A simple online ordering system for neighborhood pizza shops. One shop, one menu, take orders, basic checkout.

**Problem:** Pizza shops have no online presence or use outdated platforms. Customers want to order online.

**Target User:** Non-technical pizza shop owner (or one tech-savvy employee).

**Value Prop:** A simple, zero-maintenance ordering system. No contracts, no monthly fees, just open the link and take orders.

## Scope Split

### In Scope for Tier 1 (MVP — Ship Now)
- ✅ Menu display (items, prices, descriptions)
- ✅ Add to cart functionality
- ✅ Order submission
- ✅ Basic payment (Stripe)
- ✅ Order confirmation email
- ✅ Admin: simple order list

**Tech:**
- Frontend: React (TypeScript)
- Backend: Node.js + Express
- Database: Simple JSON file or SQLite
- Deployment: Vercel + Firebase

**Timeline:** 1-2 weeks (currently Iteration 2, blocked on payment)

### In Scope for Tier 2 (Future — After MVP Validates)
- 📋 Analytics (orders/day, revenue, popular items)
- 👥 Team member accounts + roles
- 🗺️ Delivery tracking (optional)
- 🔔 Notifications (order ready, out for delivery)
- 🖼️ Photo gallery for menu items
- 💳 Multiple payment methods

### Out of Scope for Now
- ❌ Multi-location support
- ❌ Inventory management
- ❌ Complex scheduling
- ❌ Integration with POS systems
- ❌ Enterprise features

## Success Measures (v1)
- First order successfully placed + paid
- Shop owner can update menu + see orders
- Under 5 minutes to set up
- Zero bugs on first 10 orders
