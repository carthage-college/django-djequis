# see:
# https://www.twilio.com/docs/api/messaging/message#delivery-related-errors
#

MESSAGE_DELIVERY = {
    30001:  """
            You tried to send too many messages too quickly and your
            message queue overflowed. Try sending your message again
            after waiting some time.
    """,
    30002:  """
            Your account was suspended between the time of message send
            and delivery. Please contact Twilio.
    """,
    30003:  """
            The destination handset you are trying to reach is switched
            off or otherwise unavailable.
    """,
    30004:  """
            The destination number you are trying to reach is blocked
            from receiving this message (e.g. due to blacklisting).
    """,
    30005:  """
            The destination number you are trying to reach is unknown
            and may no longer exist.
    """,
    30006:  """
            The destination number is unable to receive this message.
            Potential reasons could include trying to reach a landline or,
            in the case of short codes, an unreachable carrier.
    """,
    30007:  """
            Your message was flagged as objectionable by the carrier.
            In order to protect their subscribers, many carriers have
            implemented content or spam filtering.
    """,
    30008:  """
            The error does not fit into any of the above categories.
    """,
    30009:  """
            One or more segments associated with your multi-part
            inbound message was not received.
    """,
    30010:  "The price of your message exceeds the max price parameter."
}
