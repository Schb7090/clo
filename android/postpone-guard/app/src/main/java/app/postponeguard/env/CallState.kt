package app.postponeguard.env

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.media.AudioManager
import android.os.Build
import android.telephony.PhoneStateListener
import android.telephony.TelephonyCallback
import android.telephony.TelephonyManager
import java.util.concurrent.Executor

/**
 * Tracks whether a call is ringing or active. Telephony calls come from
 * TelephonyManager (needs READ_PHONE_STATE); VoIP calls are caught through the
 * audio mode. [onChange] fires on every telephony state change.
 */
class CallState(private val context: Context, private val executor: Executor, private val onChange: () -> Unit) {
    private val telephony = context.getSystemService(TelephonyManager::class.java)
    private val audio = context.getSystemService(AudioManager::class.java)

    @Volatile private var telephonyState: Int? = null
    private var callback: Any? = null

    fun start() {
        if (!hasPermission()) return
        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                val cb = object : TelephonyCallback(), TelephonyCallback.CallStateListener {
                    override fun onCallStateChanged(state: Int) = update(state)
                }
                telephony.registerTelephonyCallback(executor, cb)
                callback = cb
            } else {
                @Suppress("DEPRECATION")
                val l = object : PhoneStateListener() {
                    @Deprecated("Deprecated in Java")
                    override fun onCallStateChanged(state: Int, phoneNumber: String?) = update(state)
                }
                @Suppress("DEPRECATION")
                telephony.listen(l, PhoneStateListener.LISTEN_CALL_STATE)
                callback = l
            }
        } catch (e: SecurityException) {
            telephonyState = null
        }
    }

    fun stop() {
        val cb = callback ?: return
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S && cb is TelephonyCallback) {
            telephony.unregisterTelephonyCallback(cb)
        } else if (cb is PhoneStateListener) {
            @Suppress("DEPRECATION")
            telephony.listen(cb, PhoneStateListener.LISTEN_NONE)
        }
        callback = null
    }

    private fun update(state: Int) {
        telephonyState = state
        onChange()
    }

    /** true / false, or null if the call state cannot be read. */
    fun inCall(): Boolean? {
        val mode = audio.mode
        if (mode == AudioManager.MODE_IN_CALL || mode == AudioManager.MODE_IN_COMMUNICATION ||
            mode == AudioManager.MODE_RINGTONE
        ) return true
        if (!hasPermission()) return null
        val state = telephonyState ?: try {
            @Suppress("DEPRECATION")
            telephony.callState
        } catch (e: SecurityException) {
            return null
        }
        return state != TelephonyManager.CALL_STATE_IDLE
    }

    private fun hasPermission() =
        context.checkSelfPermission(Manifest.permission.READ_PHONE_STATE) == PackageManager.PERMISSION_GRANTED
}
