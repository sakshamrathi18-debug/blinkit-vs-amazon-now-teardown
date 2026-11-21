"""Offline tests: no phone needed, nothing is sent to a device."""
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import qc_audit as q
BL, AM = q.APPS["blinkit"], q.APPS["amazon"]
PK = set(q.APPS.values())

def n(pkg=BL, rid="", text="", desc="", cls="android.view.View", b=(0,0,100,100), parent=None, checkable=False):
    return dict(pkg=pkg, rid=rid, text=text, desc=desc, cls=cls, clickable=True, checkable=checkable, focused=False,
                l=b[0], t=b[1], r=b[2], b=b[3], parent=parent)
def chk(nodes, x=50, y=50): return q.check_tap(nodes, x, y, PK)
CART = n(text="Bill details", b=(0,1000,300,1050))     # puts the screen in cart/checkout mode

class Browse(unittest.TestCase):
    def no(self, nodes, x=50, y=50): self.assertFalse(chk(nodes, x, y)[0], chk(nodes, x, y))
    def yes(self, nodes, x=50, y=50): self.assertTrue(chk(nodes, x, y)[0], chk(nodes, x, y))
    def test_missing_dump(self): self.no([])
    def test_other_app(self): self.no([n(pkg="com.whatsapp")])
    def test_place_order(self):
        for l in ("Place Order", "Place your order", "PLACE ORDER"): self.no([n(text=l)])
    def test_pay_rupee(self):
        for l in ("Pay ₹243", "Pay Rs 243", "Pay ₹1,204 now"): self.no([n(text=l)])
    def test_slide_to_pay(self):
        for l in ("Slide to pay", "Swipe to pay ₹100"): self.no([n(desc=l)])
    def test_buy_now(self): self.no([n(text="Buy Now")])
    def test_proceed_to_pay(self): self.no([n(text="Proceed To Pay")])
    def test_join_prime(self):
        for l in ("Join Prime", "Try Prime free", "Get Prime", "Blinkit Pass", "Join membership"): self.no([n(text=l)])
    def test_cod_upi_card(self):
        for l in ("Cash on Delivery", "Add UPI", "Add new card", "Wallet", "Netbanking"): self.no([n(text=l)])
    def test_consent_login_address(self):
        for l in ("Accept", "I agree", "Sign in", "Log out", "Add address", "Change", "Allow"): self.no([n(text=l)])
    def test_long_label_starting_with_deny(self): self.no([n(desc="Pay on delivery available for orders above 500 rupees in your area today")])
    def test_container_with_denied_child(self):
        self.no([n(b=(0,0,500,200)), n(text="Place Order", b=(10,10,200,100), parent=0)])
    def test_rid(self): self.no([n(rid=BL+":id/place_order_btn")])
    def test_toggle(self): self.no([n(text="Donate", checkable=True)]); self.no([n(cls="android.widget.Switch")])
    def test_nothing_small_under_point(self): self.no([n(b=(0,0,1080,2400))])
    def test_wishlist_save_follow(self):
        for l in ("Add to wishlist", "Save for later", "Follow", "Notify me"): self.no([n(text=l)])
    def test_add_to_cart_ok(self): self.yes([n(text="ADD")])
    def test_product_card_ok(self): self.yes([n(desc="Amul Taaza Toned Fresh Milk 500 ml, Rs 29, 10 mins")])
    def test_search_and_tabs_ok(self):
        for l in ("Search", "Categories", "Home", "Cart"): self.yes([n(text=l)])
    def test_unlabelled_icon_ok_when_browsing(self): self.yes([n()])

class Checkout(unittest.TestCase):
    def no(self, tap, x=50, y=50): self.assertFalse(chk([CART, tap], x, y)[0], chk([CART, tap], x, y))
    def yes(self, tap, x=50, y=50): self.assertTrue(chk([CART, tap], x, y)[0], chk([CART, tap], x, y))
    def test_marker_detection(self):
        self.assertTrue(q.checkout_screen([n(text="Grand total ₹243")]))
        self.assertFalse(q.checkout_screen([n(text="Fresh vegetables")]))
    def test_unlabelled_button_refused(self): self.no(n())
    def test_unlabelled_button_with_labelled_child_uses_child(self):
        self.assertTrue(chk([CART, n(b=(0,0,300,100)), n(text="Proceed", b=(10,10,200,90), parent=1)], 50, 50)[0])
    def test_unlisted_label_refused(self):
        for l in ("Apply coupon", "Add", "Select address", "Use this address", "Deliver here", "Add tip 20"): self.no(n(text=l))
    def test_allowlist(self):
        for l in ("Proceed", "Proceed to Buy", "Proceed to checkout", "View cart", "Remove", "Delete", "Back", "Navigate up", "+", "-", "−", "Decrease quantity"):
            self.yes(n(desc=l))
    def test_pay_stays_denied(self):
        for l in ("Pay ₹243", "Place your order", "Proceed to Pay", "Slide to pay"): self.no(n(text=l))
    def test_commit_screen_detected(self):
        self.assertTrue(q.commit_visible([n(text="Place your order")]))
        self.assertTrue(q.commit_visible([n(text="Pay ₹243")]))
        self.assertFalse(q.commit_visible([n(text="Proceed")]))


class Tree(unittest.TestCase):
    def test_unrelated_pay_sibling_does_not_block(self):
        bar = n(cls="android.view.ViewGroup", b=(0,0,1080,300)); bar["clickable"] = False
        pay = n(text="Pay", b=(0,100,200,280), parent=0); now = n(text="Now", b=(300,100,500,280), parent=0)
        self.assertTrue(chk([bar, pay, now], 400, 200)[0])
        self.assertFalse(chk([bar, pay, now], 100, 200)[0])
    def test_clickable_wrapper_with_place_order_blocks_icon_tap(self):
        btn = n(b=(0,0,600,200)); icon = n(b=(10,10,60,60), parent=0); lab = n(text="Place Order", b=(100,10,500,60), parent=0)
        self.assertFalse(chk([btn, icon, lab], 30, 30)[0])
    def test_hidden_zero_size_nodes_ignored(self):
        card = n(b=(0,0,500,300)); hidden = n(text="Pay", b=(0,0,0,0), parent=0)
        self.assertTrue(chk([card, hidden], 50, 50)[0])

class Cards(unittest.TestCase):
    def test_card_with_heart_and_add(self):
        card = n(b=(0,0,600,800)); heart = n(desc="Add to wishlist", b=(500,10,590,90), parent=0); add = n(text="ADD", b=(400,700,590,780), parent=0)
        self.assertTrue(chk([card, heart, add], 500, 740)[0])
        self.assertFalse(chk([card, heart, add], 540, 50)[0])
    def test_card_with_prime_badge_ok(self):
        card = n(b=(0,0,600,800)); badge = n(desc="Prime", b=(10,10,100,60), parent=0); add = n(text="Add to cart", b=(400,700,590,780), parent=0)
        self.assertTrue(chk([card, badge, add], 500, 740)[0])
    def test_card_wrapping_pay_now_blocks(self):
        card = n(b=(0,0,600,200)); icon = n(b=(10,10,60,60), parent=0); lab = n(text="Pay now", b=(100,10,500,60), parent=0)
        self.assertFalse(chk([card, icon, lab], 30, 30)[0])

class Covered(unittest.TestCase):
    def test_button_hidden_under_footer_with_place_order(self):
        scr = n(text="Bill details", b=(0,0,1080,2400)); scr["clickable"] = False
        dec = n(desc="Decrease quantity", b=(500,2150,600,2250))                       # drawn first, scrolled under the footer
        footer = n(b=(0,2100,1080,2400)); po = n(text="Place Order", b=(600,2150,1060,2300), parent=2)   # drawn later = on top
        self.assertFalse(chk([scr, dec, footer, po], 550, 2200)[0])
    def test_visible_decrease_still_allowed(self):
        cart = n(text="Bill details", b=(0,1000,300,1050))
        dec = n(desc="Decrease quantity", b=(500,500,600,600))
        self.assertTrue(chk([cart, dec], 550, 550)[0])
    def test_footer_without_commit_text_blocked_by_allowlist_on_checkout(self):
        cart = n(text="Bill details", b=(0,1000,300,1050))
        dec = n(desc="Decrease quantity", b=(500,2150,600,2250)); footer = n(text="Delivering to Home", b=(0,2100,1080,2400))
        self.assertFalse(chk([cart, dec, footer], 550, 2200)[0])

class Footer(unittest.TestCase):
    def test_item_button_inside_sticky_bar_refused(self):
        cart = n(text="Bill details", b=(0,1000,300,1050))
        bar = n(b=(0,2034,1080,2171)); addr = n(text="Delivering to Home", b=(134,2056,476,2104), parent=1)
        dec = n(desc="Decrease quantity", b=(854,1991,905,2081))      # y=2036 falls inside the bar
        self.assertFalse(chk([cart, bar, addr, dec], 879, 2036)[0])
    def test_item_button_above_bar_ok(self):
        cart = n(text="Bill details", b=(0,1000,300,1050))
        bar = n(b=(0,2034,1080,2171)); addr = n(text="Delivering to Home", b=(134,2056,476,2104), parent=1)
        dec = n(desc="Decrease quantity", b=(854,1500,905,1590))
        self.assertTrue(chk([cart, bar, addr, dec], 879, 1545)[0])

class ScrolledCheckout(unittest.TestCase):
    def test_footer_alone_marks_checkout_and_blocks_covered_tap(self):
        bar = n(b=(0,2034,1080,2171)); addr = n(text="Delivering to Home", b=(134,2056,476,2104), parent=0)
        dec = n(desc="Decrease quantity", b=(854,1991,905,2081))
        self.assertTrue(q.checkout_screen([bar, addr, dec]))
        self.assertFalse(chk([bar, addr, dec], 879, 2036)[0])
    def test_scrolled_checkout_allows_visible_decrease(self):
        bar = n(b=(0,2034,1080,2171)); addr = n(text="Delivering to Home", b=(134,2056,476,2104), parent=0)
        dec = n(desc="Decrease quantity", b=(854,900,905,990))
        self.assertTrue(chk([bar, addr, dec], 879, 945)[0])

class Misc(unittest.TestCase):
    def test_safe_query(self):
        for s in ("amul taaza milk 500ml", "type c fast charger"): self.assertTrue(q.SAFE_WORD.fullmatch(s))
        for s in ("milk; rm -rf", "a$b", "x'y", "cold & cough"): self.assertFalse(q.SAFE_WORD.fullmatch(s))
    def test_intruders_ignore_status_bar(self):
        self.assertEqual(q.intruders([n(pkg="com.android.systemui", b=(0,0,1080,100))], PK), [])
        self.assertEqual(q.intruders([n(pkg="com.android.systemui", b=(0,500,1080,900))], PK), ["com.android.systemui"])
    def test_both_apps_allowed(self):
        self.assertEqual(q.intruders([n(pkg=BL), n(pkg=AM)], PK), [])
    def test_nodes_of_parses(self):
        x = '<hierarchy><node package="p" resource-id="r" text="Hi" content-desc="" class="c" clickable="true" checkable="false" focused="false" bounds="[0,0][10,20]"><node package="p" text="in" bounds="[1,1][2,2]"/></node></hierarchy>'
        r = q.nodes_of(x); self.assertEqual(len(r), 2); self.assertEqual(r[1]["parent"], 0)

if __name__ == "__main__": unittest.main()
