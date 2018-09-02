import string
from enum import Enum
import re
import time
from threading import Timer
import sys
from random import randint


class Status(Enum):
    available = 0
    held = 1
    reserved = 2


class Location:
    def __init__(self, row=0, column=0):
        self.row = row
        self.column = column


class Reservation:
    def __init__(self, email, seats):
        self.email = email
        self.seats = seats


class SeatHold:
    def __init__(self, seat, timer=time.time()):
        self.seat = seat
        self.timer = timer


class Seat:
    def __init__(self, status=Status.available, location=Location()):
        self.status = status
        self.location = location

    def __str__(self):
        return_string = "Seat at row: " + str(self.location.row) + " column: " + str(self.location.column)
        return_string = return_string + " is "
        if self.status is Status.available:
            return_string = return_string + "available"
        elif self.status is Status.held:
            return_string = return_string + "being held"
        else:
            return_string = return_string + "has been reserved"
        return return_string

    @property
    def is_reserved(self):
        return self.status is Status.reserved

    @property
    def is_held(self):
        return self.status is Status.held

    def is_available(self):
        return self.status is Status.available

    def get_row(self):
        return self.location.row

    def get_column(self):
        return self.location.column

    def hold_seat(self):
        self.status = Status.held

    def reserve_seat(self, email):
        self.status = Status.reserved

    def free_seat(self):
        self.status = Status.available


class Venue:
    def __init__(self, num_rows, seats_per_row):
        self.num_rows = num_rows
        self.seats_per_row = seats_per_row
        self.venue_seat_arrangement = self.create_venue()
        self.total_seats = num_rows * seats_per_row
        self.iter_current_row = 0
        self.iter_current_column = 0

    def __iter__(self):
        self.iter_current_column = 0
        self.iter_current_row = 0
        return self

    def __next__(self):
        if self.iter_current_row >= self.num_rows:
            raise StopIteration()
        elif self.iter_current_row < self.num_rows and self.iter_current_column is self.seats_per_row:
            self.iter_current_row = self.iter_current_row + 1
            self.iter_current_column = 0

        return_value = self.venue_seat_arrangement[self.iter_current_row][self.iter_current_column]
        self.iter_current_column = self.iter_current_column + 1

        return return_value

    def total_seats_available(self):
        return self.total_seats

    def create_venue(self):
        if self.num_rows is not 0 and self.seats_per_row is not 0:
            current_row = 0
            all_seats = list(list())
            while current_row < self.num_rows:
                all_seats.append(list())
                for i in range(self.seats_per_row):
                    all_seats[current_row].append(Seat(location=Location(current_row, i)))
                current_row = current_row + 1
            return all_seats

    def display_venue(self):
        if self.num_rows <= 26:
            for i in range(self.num_rows):
                row_name = string.ascii_uppercase[i]
                for j in range(self.seats_per_row):
                    if self.venue_seat_arrangement[i][j].is_available():
                        print(row_name + str(j + 1) + " ", end="")
                    else:
                        print("x ", end="")
                print()

    @staticmethod
    def seat_number_interpreter(seat_name):
        regex = re.compile("([a-zA-Z]+)([0-9]+)")
        groups = regex.match(seat_name).groups()
        if groups and len(groups) is 2:
            column_number = int(groups[1]) - 1
            row_name = groups[0].upper()
            if len(row_name) > 1:
                row_number = int(
                    string.ascii_uppercase.index(row_name[0]) * 26 + string.ascii_uppercase.index(row_name[1]))
            else:
                row_number = int(string.ascii_uppercase.index(row_name[0]))
            return row_number, column_number
        else:
            return None

    def find_and_hold_seats(self, seat_name, email):
        seat_index = self.seat_number_interpreter(seat_name)
        if seat_index[0] <= self.num_rows and seat_index[1] <= self.seats_per_row:
            row = seat_index[0]
            column = seat_index[1]
            seat = self.venue_seat_arrangement[row][column]
            seat.hold_seat()
            print(seat_name + " is being held for " + email)
            self.total_seats = self.total_seats - 1
            return seat
        else:
            print("invalid seat number")
            return None

    def hold_a_seat(self, seat):
        seat.hold_seat()
        self.total_seats = self.total_seats - 1

    def make_seat_available(self, seat):
        row = seat.get_row()
        column = seat.get_column()
        self.total_seats = self.total_seats + 1
        self.venue_seat_arrangement[row][column].free_seat()


class TicketService:
    def __init__(self):
        self.venue = Venue(4, 5)
        self.seats_being_held_dictionary = {}
        self.reserved_seats = {}
        self.hold_time = 120
        self.hold_check_polling_timer = Timer(2, self.check_hold)
        self.schedule_check_hold()

    def num_seats_available(self):
        return self.venue.total_seats_available()

    def find_and_hold_a_seat(self, seat_name, email):
        seat = self.venue.find_and_hold_seats(seat_name, email)
        if seat is not None:
            if email in self.seats_being_held_dictionary:
                self.seats_being_held_dictionary[email].append(SeatHold(seat))

    def find_and_hold_seats(self, num_seats, customer_email):
        if num_seats <= self.num_seats_available():
            seats_being_held = []
            venue_iterator = iter(self.venue)
            counter = 0
            while counter < num_seats:
                seat = next(venue_iterator)
                if seat.is_available():
                    self.venue.hold_a_seat(seat)
                    seats_being_held.append(SeatHold(seat))
                    counter = counter + 1
            self.seats_being_held_dictionary[customer_email] = seats_being_held

    def generate_unique_confirmation_number(self):
        confirmation_number = randint(10000, 99999)
        while confirmation_number in self.reserved_seats:
            confirmation_number = randint(10000, 99999)
        return confirmation_number

    def reserve_seat(self, email):
        if email in list(self.seats_being_held_dictionary):
            reserved_seats = []
            for seat_hold in self.seats_being_held_dictionary[email][:]:
                seat = seat_hold.seat
                seat.reserve_seat(email)
                reserved_seats.append(seat)
            confirmation_number = self.generate_unique_confirmation_number()
            print("your confirmation number is: " + str(confirmation_number))
            self.reserved_seats[confirmation_number] = Reservation(email, reserved_seats)
            self.seats_being_held_dictionary.pop(email)

    def check_hold(self):
        for email in list(self.seats_being_held_dictionary):
            seats_being_held = self.seats_being_held_dictionary[email]

            for seat_hold in seats_being_held[:]:
                # for i in range(len(seats_being_held)):
                if (time.time() - seat_hold.timer) >= self.hold_time:
                    self.venue.make_seat_available(seat_hold.seat)
                    seats_being_held.remove(seat_hold)
            if len(seats_being_held) is 0:
                self.seats_being_held_dictionary.pop(email)
        self.hold_check_polling_timer.run()

    def schedule_check_hold(self):
        self.hold_check_polling_timer.start()

    def stop_checking_holds(self):
        self.hold_check_polling_timer.cancel()

    def display_venue(self):
        self.venue.display_venue()

    def display_reservation(self, confirmation_number):
        confirmation_number = int(confirmation_number)
        if confirmation_number in self.reserved_seats:
            reservation = self.reserved_seats[confirmation_number]
            for seat in reservation.seats:
                print(seat)
        else:
            print("Invalid confirmation number")

    def display_hold(self, email):
        if email in self.seats_being_held_dictionary:
            seat_holds = self.seats_being_held_dictionary[email]
            for seat_hold in seat_holds:
                print(str(seat_hold.seat) + " is being held for " + str(
                    self.hold_time - (time.time() - seat_hold.timer)) + " more seconds")
        else:
            print("Email address was not found")


def main():
    ticket_service = TicketService()
    while True:
        print("--------------------------------------------------------------------------")
        print("Welcome to Walmart Labs Ticket Service. Choose from an option below: ")
        print("1. Find number of seats available")
        print("2. Hold a specific number of random seats")
        print("3. Hold a specific seat")
        print("4. Reserve seats being held")
        print("5. Display Reservation")
        print("6. Display Hold")
        print("7. Display seating")
        print("8. Exit Program")
        print("--------------------------------------------------------------------------")
        choice = input("Enter your choice #: ")


        if choice is "1":
            print("Total number of seats available: " + str(ticket_service.num_seats_available()))
        elif choice is "2":
            num_seats = int(input("Enter number of seats: "))
            email = input("Enter your email address: ")
            ticket_service.find_and_hold_seats(num_seats, email)
        elif choice is "3":
            ticket_service.display_venue()
            seat_name = input("Enter seat number: ")
            email = input("Enter your email address: ")
            ticket_service.find_and_hold_a_seat(seat_name, email)
        elif choice is "4":
            email = input("Enter your email address: ")
            ticket_service.reserve_seat(email)
        elif choice is "5":
            confirmation_number = input("Enter confirmation number: ")
            ticket_service.display_reservation(confirmation_number)
        elif choice is "6":
            email = input("Enter your email address: ")
            ticket_service.display_hold(email)
        elif choice is "7":
            ticket_service.display_venue()
        elif choice is "8":
            print("Thank you for using Walmart Ticket Service")
            ticket_service.stop_checking_holds()
            sys.exit()


if __name__ == '__main__':
    main()
