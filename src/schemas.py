"""Response models. Strict mode rejects coerced types (e.g. a price sent back as a string),
and `extra="forbid"` catches unexpected fields."""

from datetime import date

from pydantic import BaseModel, ConfigDict


class StrictModel(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")


class BookingDates(StrictModel):
    checkin: date
    checkout: date


class Booking(StrictModel):
    firstname: str
    lastname: str
    totalprice: int
    depositpaid: bool
    bookingdates: BookingDates
    additionalneeds: str | None = None


class CreatedBooking(StrictModel):
    bookingid: int
    booking: Booking


class BookingId(StrictModel):
    bookingid: int


class Token(StrictModel):
    token: str


class AuthFailure(StrictModel):
    reason: str
