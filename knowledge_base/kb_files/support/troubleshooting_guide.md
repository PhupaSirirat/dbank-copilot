# dBank Troubleshooting Guide

**Last Updated:** October 2025  
**Version:** 2.1  
**For:** Customer support and self-service

---

## Quick Issue Index

- [Login & Authentication](#login--authentication)
- [Balance & Transaction Issues](#balance--transaction-issues)
- [Transfer Problems](#transfer-problems)
- [Loan Application Issues](#loan-application-issues)
- [Interest & Calculation](#interest--calculation)
- [App Performance](#app-performance)
- [Payment Failures](#payment-failures)

---

## Login & Authentication

### Cannot Login - "Invalid Credentials"

**Symptoms:** Login fails with "Invalid username or password" error

**Common Causes:**
1. Incorrect password (most common)
2. Account temporarily locked (3 failed attempts)
3. Caps Lock enabled
4. Password expired (90-day policy)

**Solutions:**

**Step 1:** Verify credentials
- Check Caps Lock is OFF
- Ensure correct email/phone number
- Try "Show Password" to verify typing

**Step 2:** Reset password
1. Click "Forgot Password"
2. Enter registered email/phone
3. Receive OTP via SMS
4. Create new password (min 8 characters, 1 uppercase, 1 number, 1 special char)

**Step 3:** If still failing
- Account may be locked (wait 30 minutes)
- Contact support: 1-800-DBANK
- Verify identity for immediate unlock

---

### Biometric Login Not Working

**Symptoms:** Face ID / Fingerprint fails repeatedly

**Common Causes:**
1. App version 1.2.0-1.2.1 (known bug)
2. Biometric data changed on device
3. Permission not granted
4. Device encryption key rotated

**Solutions:**

**For v1.2 users:**
1. Update app to v1.3.0 or later (CRITICAL)
2. Re-enable biometrics after update

**For v1.3+ users:**
1. Settings → Security → Biometric Login → OFF
2. Log out completely
3. Log in with PIN/password
4. Re-enable biometric login
5. Re-register fingerprint/face

**iOS Specific:**
- Settings → Face ID & Passcode → dBank → Enable
- Ensure Face ID works in other apps first

**Android Specific:**
- Settings → Biometrics → Fingerprints → Re-add
- Clear app cache: Settings → Apps → dBank → Storage → Clear Cache

---

### "Session Expired" Error

**Symptoms:** Logged out unexpectedly, "Session expired" message

**Common Causes:**
1. Session timeout (15 minutes inactivity)
2. Multiple device logins
3. IP address change (VPN)
4. Server-side security lockout

**Solutions:**
1. Simply log in again (normal behavior)
2. If using VPN: Disconnect and retry
3. If frequent logouts: Check app version (update if < v1.3.0)
4. For security lockout: Contact support

**Prevention:**
- Keep app active during transactions
- Complete transactions within 15 minutes
- Disable VPN for banking app
- Don't share login credentials

---

## Balance & Transaction Issues

### Balance Not Updating

**Symptoms:** Balance shows old amount, doesn't reflect recent transaction

**Common Causes:**
1. Cache not refreshed
2. Transaction still pending
3. App version 1.2.0 (known issue)
4. Network delay

**Solutions:**

**Step 1:** Manual refresh
- Pull down on screen to refresh
- Wait 5 seconds
- Check if balance updates

**Step 2:** Check transaction status
- Go to Transaction History
- Look for "Pending" transactions
- Wait for transaction to complete (usually <5 minutes)

**Step 3:** Force app refresh
1. Close app completely (swipe away)
2. Reopen app
3. Balance should update

**Step 4:** Clear cache (if balance still wrong)
- Settings → Storage → Clear Cache
- Log out and log in again

**Step 5:** If balance still incorrect
- Note exact amount discrepancy
- Contact support with transaction reference
- Check web portal for accurate balance

**Known Issue:** v1.2.0 users - Upgrade to v1.3.0 immediately

---

### Transaction History Missing

**Symptoms:** Cannot see transactions older than 7-30 days

**Affected Versions:** v1.2.0 (critical bug), partially v1.2.1

**Solutions:**

**If using v1.2.0 or v1.2.1:**
1. **UPDATE TO v1.3.0 IMMEDIATELY**
2. Transaction history automatically restored
3. No data was lost (display issue only)

**If using v1.3.0+:**
1. Pull down to refresh
2. Tap "Load More" at bottom
3. Clear app cache if not loading
4. Use web portal for full history export

**Download transaction history:**
- Settings → Statements → Request Statement
- Choose date range (up to 2 years)
- Receive PDF via email within 30 minutes

---

### Duplicate Transactions Showing

**Symptoms:** Same transaction appears twice in history

**Common Causes:**
1. Display glitch (not actually duplicate charged)
2. Pending + Completed showing separately
3. Reversal + Original transaction both showing

**How to Verify:**
1. Check transaction times - if identical, it's a display issue
2. Check actual balance - should match if only one charged
3. Wait 24 hours - duplicates usually resolve automatically
4. Check transaction status (pending vs completed)

**Solutions:**
- If actual balance correct: Ignore duplicate display
- If actually charged twice: Contact support immediately
- Provide: Transaction date, amount, merchant name, reference number

**Note:** True duplicate charges are rare (<0.01% of transactions) and reversed automatically within 48 hours.

---

## Transfer Problems

### Transfer Failed - "Insufficient Balance"

**Symptoms:** Transfer rejected even though balance seems sufficient

**Common Causes:**
1. Pending transactions not reflected
2. Hold amount from previous authorization
3. Daily limit reached
4. Available balance < Total balance

**Checking Available Balance:**
1. Dashboard → Account → View Details
2. "Available Balance" (not "Total Balance")
3. Available = Total - Pending - Holds

**Solutions:**

**Step 1:** Wait for pending transactions to clear (5-15 minutes)

**Step 2:** Check holds
- Recent card authorizations hold funds 3-5 days
- Check-in transactions hold 7-30 days
- Pending loan EMI deductions

**Step 3:** Check daily limits
- Savings accounts: 500K THB/day (dSave Plus), 2M THB/day (dSave Premium)
- Limits reset at midnight
- Check limit usage: Settings → Transfer Limits

**Step 4:** If none of above apply
- Contact support for hold release
- Provide transaction details

---

### Transfer Stuck at "Processing"

**Symptoms:** Transfer shows processing for >1 hour

**Expected Processing Times:**
- Internal transfers: Instant
- Other dBank accounts: <5 minutes  
- Other banks (PromptPay): <30 minutes
- Other banks (regular): 1-24 hours

**Solutions:**

**For transfers <24 hours old:**
1. Wait - may still be processing
2. Check recipient's account
3. Transaction reference for tracking

**For transfers >24 hours old:**
1. Contact support immediately
2. Provide transfer reference number
3. Likely stuck in intermediary bank
4. Support can investigate and expedite

**Prevention:**
- Double-check recipient details
- Use PromptPay for faster transfers
- Transfer during business hours for same-day processing

---

### Cannot Add External Account

**Symptoms:** "Unable to verify account" error when adding external bank account

**Common Causes:**
1. Incorrect account number/IFSC
2. Account name mismatch
3. Account closed/frozen at other bank
4. KYC verification pending

**Solutions:**

**Step 1:** Verify details
- Account number (no spaces or hyphens)
- IFSC/SWIFT code exact match
- Account holder name exactly as in bank records

**Step 2:** Verify using micro-deposit
1. dBank sends small amount (1-5 THB)
2. Check other bank account for deposit
3. Enter exact amount in dBank app
4. Account verified

**Step 3:** If verification fails
- Contact other bank to confirm account active
- Ensure account name matches your dBank KYC name
- For joint accounts: Add as primary holder only

---

## Loan Application Issues

### Application Stuck at "Processing"

**Symptoms:** Loan application doesn't move beyond processing stage

**Known Issue:** v1.2.0-v1.2.1 (critical bug - UPGRADE IMMEDIATELY)

**Expected Processing Times:**
- dLoan Quick: 5 minutes (instant approval)
- dLoan Flexi: 1-24 hours
- Above 500K THB: Up to 48 hours

**Solutions:**

**If using v1.2.0 or v1.2.1:**
1. **UPDATE TO v1.3.0** - This fixes stuck applications
2. Existing stuck applications processed automatically after update
3. Or contact loans@dbank.co.th for manual processing

**If using v1.3.0+ and stuck:**
1. Check email for document requests
2. Verify all documents uploaded correctly
3. Check application status on web portal
4. If >48 hours: Contact loans@dbank.co.th with application reference

**Document Issues:**
- Ensure documents are clear, not blurry
- File size <5MB each
- Accepted formats: PDF, JPG, PNG
- Recent documents (within 3 months)

---

### Loan Rejected - Why?

**Common Rejection Reasons:**

1. **Credit Score** (40% of rejections)
   - Score below 600
   - Recent defaults/late payments
   - High debt-to-income ratio

2. **Income Insufficient** (25%)
   - Below minimum requirement (15K for Quick, 30K for Flexi)
   - Cannot verify income
   - Unstable income source

3. **Employment** (20%)
   - Less than required tenure
   - High-risk industry
   - Cannot verify employment

4. **Documentation** (10%)
   - Incomplete documents
   - Documents expired
   - Unable to verify identity

5. **Other** (5%)
   - Already have maximum loans
   - Court cases pending
   - Negative regulatory database match

**What to Do:**
1. Check rejection email for specific reason
2. Improve credit score (pay existing debts, wait 3-6 months)
3. Reapply with complete documentation
4. Consider lower loan amount
5. Add co-applicant if eligible

**Credit Score Improvement:**
- Pay all bills on time for 6 months
- Reduce credit card utilization below 30%
- Don't apply for multiple loans simultaneously
- Check credit report for errors

---

## Interest & Calculation

### Interest Not Credited

**Symptoms:** Monthly interest not showing in savings account

**CRITICAL:** v1.2.0-v1.2.1 users affected by major bug

**Solutions:**

**If using v1.2.0 or v1.2.1:**
1. **UPDATE TO v1.3.0 IMMEDIATELY**
2. Interest automatically backdated within 3 business days
3. Check email for compensation details (additional 0.5% interest)

**If using v1.3.0+ and interest still missing:**

**Step 1:** Verify interest credit date
- Interest credited on LAST day of month
- Check on 1st of next month if not visible on 31st

**Step 2:** Check minimum balance requirement
- dSave Plus: No minimum
- dSave Premium: Average monthly balance determines rate

**Step 3:** Calculate expected interest
- Formula: (Daily Balance × Annual Rate) / 365
- Multiply by days in month
- Compare with credited amount

**Step 4:** If interest incorrect or missing
- Note expected vs actual amount
- Contact support@dbank.co.th
- Provide account details and calculation

**Web Portal Check:**
- Log in to web.dbank.co.th
- View Detailed Statement
- Interest line items shown separately

---

### EMI Amount Seems Wrong

**Symptoms:** EMI deduction different from loan agreement

**Common Causes:**
1. Partial prepayment made (EMI recalculated)
2. Late payment fee added
3. GST/tax calculation
4. Promotional rate expired

**How to Verify:**

**Step 1:** Check loan statement
- Loans → Select Loan → View Statement
- Shows principal + interest + fees breakdown

**Step 2:** Recalculation events
- Prepayments reduce EMI or tenure
- Check for any prepayment in last 2 months
- EMI recalculation notification sent

**Step 3:** Additional charges
- Late payment fee: 500 THB
- Cheque bounce: 500 THB
- GST: 18% on interest component

**Step 4:** If still unclear
- Download loan amortization schedule
- Contact loans@dbank.co.th
- Request detailed breakdown

---

## App Performance

### App Crashes or Freezes

**Symptoms:** App closes unexpectedly or becomes unresponsive

**Quick Fixes:**

**Step 1:** Force close and reopen
- iOS: Swipe up → Swipe away dBank app → Reopen
- Android: Recent apps → Swipe away dBank → Reopen

**Step 2:** Clear app cache
- Settings → Storage → Clear Cache (NOT Clear Data)
- Reopens app

**Step 3:** Check app version
- Must be v1.3.0 or later
- Update if older version

**Step 4:** Restart device
- Turn off phone
- Wait 30 seconds
- Turn on and retry

**Step 5:** Reinstall app (last resort)
- Uninstall dBank app
- Download fresh from app store
- Log in again (data on server, won't be lost)

**If crashes persist:**
- Note when it crashes (which screen/action)
- Device model and OS version
- Email support@dbank.co.th with details

---

### Slow Performance

**Symptoms:** App takes long to load, screens lag

**Common Causes:**
1. Poor internet connection
2. Cache buildup
3. Low device storage
4. Old app version
5. Background apps consuming resources

**Solutions:**

**Step 1:** Check internet
- Test: www.speedtest.net
- Minimum required: 2 Mbps
- Switch WiFi ↔ Mobile data

**Step 2:** Clear cache
- Settings → Storage → Clear Cache
- Restart app

**Step 3:** Free up device storage
- Need minimum 1GB free space
- Delete unused apps/photos
- Check: Device Settings → Storage

**Step 4:** Close background apps
- Close all other apps
- Restart device
- Open only dBank app

**Step 5:** Update app
- Check for latest version
- Update to v1.3.0+

**Network Tips:**
- Avoid public WiFi for security
- Use stable home/office network
- Disable VPN for faster performance

---

## Payment Failures

### Auto-Debit Failed

**Symptoms:** Scheduled EMI payment not deducted on due date

**Known Issue:** v1.2.0 (critical bug - update immediately)

**Common Causes:**
1. Insufficient balance
2. Account temporarily locked
3. App v1.2.0 bug (auto-debit scheduler broken)
4. Bank maintenance

**Solutions:**

**If using v1.2.0:**
1. **UPDATE TO v1.3.0 immediately**
2. Make manual payment to avoid late fee
3. Auto-debit will work correctly after update

**If using v1.3.0+:**

**Step 1:** Check account balance
- Ensure sufficient balance 1 day before due date
- Include buffer (EMI + 500 THB extra)

**Step 2:** Verify auto-debit enabled
- Loans → Select Loan → Auto-Debit Settings
- Should show "Active"

**Step 3:** Make manual payment
- Loans → Select Loan → Make Payment
- Avoid late fee (500 THB)

**Step 4:** Contact support
- Report auto-debit failure
- Request late fee waiver (granted if app issue)

**Prevention:**
- Set reminder 2 days before EMI date
- Maintain sufficient balance
- Enable low balance alerts

---

### Card Payment Declined

**Symptoms:** Credit/debit card payment rejected

**Common Reasons:**
1. Insufficient funds/credit limit
2. Card expired
3. CVV incorrect
4. OTP not entered
5. International card blocked
6. Daily limit exceeded

**Solutions:**

**Step 1:** Verify card details
- Card number (no spaces)
- Expiry date (MM/YY format)
- CVV (3 digits back, 4 digits front for Amex)
- Cardholder name exactly as on card

**Step 2:** Check card limits
- Contact card issuing bank
- Verify sufficient balance/limit
- Check daily transaction limit

**Step 3:** Try alternative payment
- Different card
- Net banking
- UPI
- Account balance

**Step 4:** If card verified and should work
- Try after 30 minutes (may be temporary issue)
- Contact your card bank
- Enable online transactions if disabled

---

## Contact Support

**24/7 Hotline:** 1-800-DBANK (1-800-32265)  
**Email:** support@dbank.co.th  
**In-App Chat:** Fastest response (avg 5 min)  
**WhatsApp:** +66-2-1234-5678  

**For v1.2 Issues:**  
Priority hotline: 1-800-DBANKV12  
Email: v12support@dbank.co.th

---

## Related Documents
- [v1.2 Release Notes](v1.2_release_notes.md)
- [Digital Saving Guide](digital_saving_product_guide.md)
- [Digital Lending Guide](digital_lending_product_guide.md)
- [FAQ](faq.md)