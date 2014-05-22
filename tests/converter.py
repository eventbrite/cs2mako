# Copyright (c) 2014 Eventbrite, Inc. All rights reserved.
# See "LICENSE" file for license.

from cs2mako.converter import Converter


def test():
    test_string = """a b c
test 1.1: VAR
------------------------------------------------------------------------------
    <?cs var:mg.foodata.foo ?>bar

test 1.2: SET
------------------------------------------------------------------------------
        <?cs set:hide_order_and_discount = 1 ?>
						<?cs set:mg.has_children = #1 ?>


test 2.1: IF
------------------------------------------------------------------------------
<?cs if:foo ?>showthiswhentrue<?cs /if ?>
test 2.2: IF ELSE
------------------------------------------------------------------------------
<?cs if:foo ?>showthiswhentrue<?cs else ?>showthiswhenfalse<?cs /if ?>
test 2.3: IF ELIF
------------------------------------------------------------------------------
<?cs if:foo ?>showthiswhen foo<?cs elseif:bar ?>showthiswhen bar<?cs /if ?>
test 2.4: IF (nested)
------------------------------------------------------------------------------
<?cs if:foo ?>IF1<?cs if:bar ?>IF2<?cs else ?>ELS<?cs /if ?><?cs /if ?>

test 3.1: ALT
------------------------------------------------------------------------------
<?cs alt:ticket.fee_collected_override ?>foo <?cs var:var_name ?> o<?cs /alt ?>

test 4.1: INCLUDE
------------------------------------------------------------------------------
<?cs include:"forms/admin-authnet.html" ?>

test 5.1: COMMENT
------------------------------------------------------------------------------
<?cs # custom JS for the foo page ?>
       <?cs # custom JS for the foo page ?>
       <?cs # custom JS for the foo page ?><?cs var:var_name ?>bar
    <?cs # custom JS for the foo page ?>some-text
    <?cs # custom JS for the foo page ?>     some-text

test 6.1: EACH
------------------------------------------------------------------------------
<?cs each:item = mg.foodata.foo ?>x<?cs /each ?>

test 6.2: EACH
------------------------------------------------------------------------------
<?cs each:item = mg.foodata.foo ?>
	<?cs if:!item.is_on ?>
		<?cs set:mg.noton = mg.noton + #1 ?>
	<?cs /if ?>
<?cs /each ?>



test 7.1: LOOP
------------------------------------------------------------------------------
	<?cs loop:x = 1,5 ?>x<?cs /loop ?>

test 7.2: LOOP
------------------------------------------------------------------------------
	<?cs loop:x = item.minimum, item.max_per, #1 ?>
		<?cs if:x>0 && some_exception ?>
		<option value="<?cs var:x ?>" <?cs if:x == item.defaultquantity ?>selected<?cs /if ?>><?cs var:x ?><?cs if:item.limit < 10 ?>&nbsp;<?cs /if ?></option>
		<?cs /if ?>
	<?cs /loop ?>




test 20: FINAL LINE
------------------------------------------------------------------------------
<EOF>
"""
    # import pprint
    # def parse(s):
    #     for line in s.split('\n'):
    #         tokens = scanner.scan(line)[0]
    #         for token in tokens:
    #             yield token
    # last_char = None
    # for token in parse(test_string):
    #     if isinstance(token, Char):
    #         print token.token,
    #     else:
    #         print token.token

    converter = Converter(test_string)
    converter.convert()
    # for n in converter.tokenize():
    #     print n

if __name__ == "__main__":
    test()
