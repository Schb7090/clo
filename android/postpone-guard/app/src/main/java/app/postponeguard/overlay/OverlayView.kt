package app.postponeguard.overlay

import android.annotation.SuppressLint
import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.RectF
import android.os.SystemClock
import android.util.TypedValue
import android.view.Gravity
import android.view.KeyEvent
import android.view.MotionEvent
import android.view.View
import android.view.ViewConfiguration
import android.widget.Button
import android.widget.FrameLayout
import android.widget.LinearLayout
import android.widget.TextView
import app.postponeguard.core.HoldDetector
import app.postponeguard.core.Item

/**
 * Opaque full-screen view: the item, DONE and SKIP TODAY. Holding a finger
 * anywhere (buttons included) for 5 seconds calls [onEscape]; a ring shows
 * the hold's progress. The back key is swallowed.
 */
@SuppressLint("ViewConstructor")
class OverlayView(
    context: Context,
    item: Item,
    private val onDone: () -> Unit,
    private val onSkip: () -> Unit,
    private val onEscape: () -> Unit,
) : FrameLayout(context) {

    private val hold = HoldDetector(
        holdMillis = 5_000,
        slopPx = ViewConfiguration.get(context).scaledTouchSlop * 4f,
    )
    private val ring = ProgressRing(context)
    private val ticker = object : Runnable {
        override fun run() {
            val t = SystemClock.uptimeMillis()
            ring.progress = hold.progress(t)
            if (hold.tick(t)) {
                ring.progress = 0f
                onEscape()
            } else if (hold.isHolding) {
                postOnAnimation(this)
            }
        }
    }

    init {
        setBackgroundColor(Color.rgb(18, 18, 24))
        isFocusable = true
        isFocusableInTouchMode = true

        val column = LinearLayout(context).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER
            setPadding(dp(32), dp(32), dp(32), dp(32))
        }
        column.addView(text("Postponed ${item.postponedDays} days", 16f, Color.rgb(255, 170, 90)))
        column.addView(text(item.title, 30f, Color.WHITE).apply { setPadding(0, dp(16), 0, dp(40)) })

        val buttons = LinearLayout(context).apply { orientation = LinearLayout.HORIZONTAL; gravity = Gravity.CENTER }
        buttons.addView(button("DONE") { onDone() })
        buttons.addView(View(context), LinearLayout.LayoutParams(dp(24), 1))
        buttons.addView(button("SKIP TODAY") { onSkip() })
        column.addView(buttons)
        column.addView(text("Hold anywhere for 5 seconds to dismiss", 13f, Color.GRAY).apply {
            setPadding(0, dp(48), 0, 0)
        })

        addView(column, LayoutParams(LayoutParams.MATCH_PARENT, LayoutParams.MATCH_PARENT))
        addView(ring, LayoutParams(dp(96), dp(96), Gravity.CENTER_HORIZONTAL or Gravity.BOTTOM).apply {
            bottomMargin = dp(64)
        })
    }

    /** The root sees every touch before its children, so the hold also works on the buttons. */
    override fun dispatchTouchEvent(ev: MotionEvent): Boolean {
        track(ev)
        return super.dispatchTouchEvent(ev)
    }

    /** Consume touches on the background so nothing reaches the app underneath. */
    @SuppressLint("ClickableViewAccessibility")
    override fun onTouchEvent(ev: MotionEvent): Boolean = true

    private fun track(ev: MotionEvent) {
        when (ev.actionMasked) {
            MotionEvent.ACTION_DOWN -> {
                hold.down(SystemClock.uptimeMillis(), ev.rawX, ev.rawY)
                removeCallbacks(ticker)
                postOnAnimation(ticker)
            }
            MotionEvent.ACTION_MOVE -> hold.move(ev.rawX, ev.rawY)
            MotionEvent.ACTION_POINTER_DOWN, MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> {
                hold.cancel()
                ring.progress = 0f
            }
        }
    }

    override fun dispatchKeyEvent(event: KeyEvent): Boolean =
        if (event.keyCode == KeyEvent.KEYCODE_BACK) true else super.dispatchKeyEvent(event)

    override fun onDetachedFromWindow() {
        removeCallbacks(ticker)
        super.onDetachedFromWindow()
    }

    private fun text(s: String, sp: Float, color: Int) = TextView(context).apply {
        text = s
        setTextSize(TypedValue.COMPLEX_UNIT_SP, sp)
        setTextColor(color)
        gravity = Gravity.CENTER
    }

    private fun button(label: String, onClick: () -> Unit) = Button(context).apply {
        text = label
        setTextSize(TypedValue.COMPLEX_UNIT_SP, 18f)
        minWidth = dp(140)
        setOnClickListener { onClick() }
    }

    private fun dp(v: Int) = (v * resources.displayMetrics.density).toInt()

    private class ProgressRing(context: Context) : View(context) {
        private val paint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            style = Paint.Style.STROKE
            strokeWidth = 8 * resources.displayMetrics.density
            strokeCap = Paint.Cap.ROUND
            color = Color.WHITE
        }
        private val box = RectF()

        var progress = 0f
            set(v) { if (field != v) { field = v; invalidate() } }

        override fun onDraw(canvas: Canvas) {
            if (progress <= 0f) return
            val inset = paint.strokeWidth
            box.set(inset, inset, width - inset, height - inset)
            canvas.drawArc(box, -90f, 360f * progress, false, paint)
        }
    }
}
