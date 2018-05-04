# RunTypes JSON File

(Mike Bottini here)

From my commit message of the `runtypes_config.json` revision:

---

Each RunType will now contain the following values:

* `args`, containing an ordered list of arguments. This is for the
purpose of dialogue and presenting each parameter to the user.

* `annotations`, containing key-value pairs of arguments and
descriptions for each one. This is for explaining each parameter
to the user.

* `types`, containing key-value pairs of arguments and types. This
is for defining valid user input for each argument.

* `translations`, containing key-value pairs of arguments and
.props values. Upon running in `main`, the program will take a Run
and its corresponding RunType and write values to its temporary
.props file.

* `props_defaults`, containing values that will be written by
default to the .props file without any user input at all.
These are intrinsic to the RunType.

For example, let's say that we have an RunType with the following:

    "SPAM" : {
      args : [
        "foo"
        "bar"
      ],

      annotations : {
        "foo" : "Lorem ipsum dolor sit amet, consectetur...",
        "bar" : "Sed blandit metus quis nulla dapibus..."
      },

      "types" : {
        "foo" : "string",
        "bar" : "integer"
      },

      "translations" : {
        "foo" : "controller.quux.spam.eggs.foo"
      },

      "props_defaults" : {
        "controller.muffin.scone" : false,
        "controller.waffle.pancake" : 50,
        "controller.bacon.sausage" : "eggs"
      }
    }

Upon a user creating a `SPAM` Run, the Dialogue will ask the user to
provide values for `foo` and `bar`, demanding a string and integer
as input, respectively. If needed, the user can obtain the annotations
(Lorem ipsum dolor sit amet...) to explain what he is supposed to input.
Let's say that he inputs `oatmeal` and `5`, respectively.

Upon running the above run, `main` will write the following to
the temporary .props file:

    controller.quux.spam.eggs.foo=oatmeal
    controller.muffin.scone=false
    controller.waffle.pancake=50
    controller.bacon.sausage=eggs

The remaining `bar` value will possibly be used in the actual JVM
invocation.

# RunList JSON File

The RunList is much simpler. Going with Benjamin Spriggs' request for more metadata,
I'm happy to provide something like the following schema:

    {
      "Runs" : [
        {
          "Tag" : "SPAM Run 1",
          "RunType" : "SPAM",
          "foo" : "oatmeal",
          "bar" : 5
        }
      ],

      "Meta" : {
        "creation_date": "2012 23 1 1",
        "name": "crepes",
        "company": "Cream of Wheat, Inc"
      }
    }

Note that `Runs` is an ordered list, as each run will be run sequentially in an
order that matters to the user.

# Putting it Together In Main

As stated above and in the meeting, `main` needs to pull from both the `RunList`
and the `RunTypes` JSON files.

* It will take the tag name from the `RunList` to create a directory with the
results.

* It will obtain the RunType of the current Run from the `RunList`.

* It will write the props file with the props attributes defined in `RunTypes`
and the values defined in the `RunList`.

* It will use a **hardcoded** function to create the JVM invocation, pulling
values from the `RunList`. Note that right now, we're just constructing
`run.sh` calls. Depending on how few arguments remain, this might not have
to be hardcoded! It might be possible to create a generic invocation with
any additional JVM Options, if necessary.

* It then invokes the JVM with this command and saves the data.