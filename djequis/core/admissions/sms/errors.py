# see error codes and descriptions:
# https://www.twilio.com/docs/api/messaging/message#delivery-related-errors
# and for status definitions:
# https://support.twilio.com/hc/en-us/articles/223134347-What-do-the-SMS-statuses-mean-


MESSAGE_DELIVERY_CODES = {
    30001:  {
        'message':      "Queue overflow",
        'description':  """
            You tried to send too many messages too quickly and your
            message queue overflowed. Try sending your message again
            after waiting some time.
        """
    },
    30002:  {
        'message':      "Account suspended",
        'description':  """
            Your account was suspended between the time of message send
            and delivery. Please contact Twilio.
        """
    },
    30003:  {
        'message':      "Unreachable destination handset",
        'description':  """
            The destination handset you are trying to reach is switched
            off or otherwise unavailable.
        """
    },
    30004:  {
        'message':      "Message blocked",
        'description':  """
            The destination number you are trying to reach is blocked
            from receiving this message (e.g. due to blacklisting).
        """
    },
    30005:  {
        'message':      "Unknown destination handset",
        'description':  """
            The destination number you are trying to reach is unknown
            and may no longer exist.
        """
    },
    30006:  {
        'message':      "Landline or unreachable carrier",
        'description':  """
            The destination number is unable to receive this message.
            Potential reasons could include trying to reach a landline or,
            in the case of short codes, an unreachable carrier.
        """
    },
    30007:  {
        'message':      "Carrier violation",
        'description':  """
            Your message was flagged as objectionable by the carrier.
            In order to protect their subscribers, many carriers have
            implemented content or spam filtering.
        """
    },
    30008:  {
        'message':      "Unknown error",
        'description':   """
            The error does not fit into any of the above categories.
        """
    },
    30009:  {
        'message':      "Missing segment",
        'description':  """
            One or more segments associated with your multi-part
            inbound message was not received.
        """
    },
    30010:  {
        'message':      "Message price exceeds max price.",
        'description':  """
            The price of your message exceeds the max price parameter.
        """
    },
}
